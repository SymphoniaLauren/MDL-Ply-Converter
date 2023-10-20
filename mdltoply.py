# MDL and the other 3D format to .ply converter
# By SymphoniaLauren

import sys
import struct
import textwrap
import os

MDL_MAGIC = b"MDL@"
PACKED_MDL_HEADER_SIZE = 0xC
PACKED_UV_ENTRY_SIZE = 0xC  # float, float, int | (u,v, rgba)
PACKED_VERTEX_ENTRY_SIZE = 0x6  # short, short, short | (x, y, z)


def convert():
    # Test wheter is a single MDL or a packed MDL
    with open(sys.argv[1], "rb") as f:

        # If MAGIC bytes match, then it's a single MDL
        if f.read(4) == MDL_MAGIC:
            convMDL()
            return

        # It did not, try and validate packed MDL
        f.seek(0)  # goto start
        filesize = os.path.getsize(sys.argv[1])
        modelcount = struct.unpack("<I", f.read(4))[0]
        trivertcount = struct.unpack("<I", f.read(4))[0]
        quadvertcount = struct.unpack("<I", f.read(4))[0]
        vertcount = trivertcount + quadvertcount

        total_bytes = (
            PACKED_MDL_HEADER_SIZE
            + (vertcount * PACKED_UV_ENTRY_SIZE)
            + (vertcount * PACKED_VERTEX_ENTRY_SIZE) * modelcount
        )

        # file size matches with header info, likely a packed MDL
        if filesize == total_bytes:
            convfieldMDL()
            return

    print("Missing MDL header or invalid input file")


def convMDL():
    # Consume the input first
    with open(sys.argv[1], "rb") as f:
        magic = f.read(4)

        # Bail out on wrong file
        if magic != MDL_MAGIC:
            print("Not an MDL file! MDLファイルではありません！")
            return

        # We get the vertice and face information here
        trivertcount = struct.unpack("<I", f.read(4))[0]
        quadvertcount = struct.unpack("<I", f.read(4))[0]
        trifacecount = trivertcount // 3
        quadfacecount = quadvertcount // 4
        vertcount = trivertcount + quadvertcount
        facecount = trifacecount + quadfacecount
        vertdatasize = vertcount * 24

        # grab the blobby because I am lazy (^^;)v
        vertdata = f.read(vertdatasize)

    print(f"Tri vertices: {trivertcount}")
    print(f"Quad vertices: {quadvertcount}")
    print(f"Triangle count: {trifacecount}")
    print(f"Quad count: {quadfacecount}")
    print(f"Total vertices: {vertcount}")
    print(f"Total faces: {facecount}")

    # get the face data information for writing
    # here we get the triangle faces
    trianglefacedata = []
    for i in range(0, trivertcount, 3):
        tristring = b"\x03" + struct.pack("<3I", i, i + 1, i + 2)
        trianglefacedata.append(tristring)

    # here we get the quad faces
    quadfacedata = []
    for i in range(trivertcount, vertcount, 4):
        quadstring = b"\x04" + struct.pack("<4I", i, i + 2, i + 3, i + 1)
        quadfacedata.append(quadstring)

    # make header
    vertexcountstring = str(vertcount).encode()
    facecountstring = str(facecount).encode()
    headerstring = (
        b"ply\n"
        b"format binary_little_endian 1.0\n"
        b"comment mdl to ply script by SymphoniaLauren\n"
        b"element vertex %b\n"
        b"property float x\n"
        b"property float y\n"
        b"property float z\n"
        b"property float s\n"
        b"property float t\n"
        b"property uchar red\n"
        b"property uchar green\n"
        b"property uchar blue\n"
        b"property uchar alpha\n"
        b"element face %b\n"
        b"property list uchar int vertex_index\n"
        b"end_header\n" % (vertexcountstring, facecountstring)
    )

    # now we write the file
    print("Writing ply...")
    output = sys.argv[2]
    with open(output, "wb+") as f:
        f.write(headerstring)

        f.write(vertdata)
        for i in trianglefacedata:
            f.write(i)
        for i in quadfacedata:
            f.write(i)

    print("File written successfully!")


def convfieldMDL():
    # consume the input here
    with open(sys.argv[1], "rb") as f:
        filesize = os.path.getsize(sys.argv[1])
        modelcount = struct.unpack("<I", f.read(4))[0]
        trivertcount = struct.unpack("<I", f.read(4))[0]
        quadvertcount = struct.unpack("<I", f.read(4))[0]
        trifacecount = trivertcount // 3
        quadfacecount = quadvertcount // 4
        vertcount = trivertcount + quadvertcount
        facecount = trifacecount + quadfacecount

        total_bytes = (
            PACKED_MDL_HEADER_SIZE
            + (vertcount * PACKED_UV_ENTRY_SIZE)
            + (vertcount * PACKED_VERTEX_ENTRY_SIZE) * modelcount
        )

        print(f"Expected file size: {total_bytes}")
        print(f"Actual file size:   {filesize}")

        # bail out on wrong file
        if filesize != total_bytes:
            print("Not a valid input! このファイルは妥当ではありません！")
            return

        print(f"Model count: {modelcount}")
        print(f"Tri vertices: {trivertcount}")
        print(f"Quad vertices: {quadvertcount}")
        print(f"Triangle count: {trifacecount}")
        print(f"Quad count: {quadfacecount}")
        print(f"Total vertices: {vertcount}")
        print(f"Total faces: {facecount}")

        # here we get the texture coordinates and the RGBA data
        s = []
        t = []
        rgba = []

        for i in range(0, vertcount):

            u = struct.unpack("<I", f.read(4))[0]
            v = struct.unpack("<I", f.read(4))[0]
            vertcolors = struct.unpack("<I", f.read(4))[0]
            s.append(u)
            t.append(v)
            rgba.append(vertcolors)

        # now we get the list of vertices for the models
        # Jesus take the wheel...

        modelsx = []
        modelsy = []
        modelsz = []

        # I'm hoping this loop works
        for _ in range(modelcount):
            x = []
            y = []
            z = []
            for __ in range(vertcount):
                xshort = struct.unpack("<H", f.read(2))[0]
                yshort = struct.unpack("<H", f.read(2))[0]
                zshort = struct.unpack("<H", f.read(2))[0]
                x.append(xshort)
                y.append(yshort)
                z.append(zshort)
            modelsx.append(x)
            modelsy.append(y)
            modelsz.append(z)

        # here we get the triangle faces
        trianglefacedata = []
        for i in range(0, trivertcount, 3):
            tristring = b"\x03" + struct.pack("<3I", i, i + 1, i + 2)
            trianglefacedata.append(tristring)

        # here we get the quad faces
        quadfacedata = []
        for i in range(trivertcount, vertcount, 4):
            quadstring = b"\x04" + struct.pack("<4I", i, i + 2, i + 3, i + 1)
            quadfacedata.append(quadstring)

    # Now we write the file(s)
    vertexcountstring = str(vertcount).encode()
    facecountstring = str(facecount).encode()

    headerstring = (
        b"ply\n"
        b"format binary_little_endian 1.0\n"
        b"comment mdl to ply script by SymphoniaLauren\n"
        b"element vertex %b\n"
        b"property short x\n"
        b"property short y\n"
        b"property short z\n"
        b"property float s\n"
        b"property float t\n"
        b"property uchar red\n"
        b"property uchar green\n"
        b"property uchar blue\n"
        b"property uchar alpha\n"
        b"element face %b\n"
        b"property list uchar int vertex_index\n"
        b"end_header\n" % (vertexcountstring, facecountstring)
    )

    for i in range(0, modelcount):
        if sys.argv[1].endswith(".ply") == True:
            output = sys.argv[1].removesuffix(".ply") + str(i) + ".ply"
        else:
            output = sys.argv[1] + str(i) + ".ply"

        with open(output, "wb+") as f:
            f.write(headerstring)

            # Here we write the vertex data
            for j in range(0, vertcount):
                f.write(struct.pack("<H", modelsx[i][j]))
                f.write(struct.pack("<H", modelsy[i][j]))
                f.write(struct.pack("<H", modelsz[i][j]))
                f.write(struct.pack("<I", s[j]))
                f.write(struct.pack("<I", t[j]))
                f.write(struct.pack("<I", rgba[j]))

            for tri in trianglefacedata:
                f.write(tri)

            for quad in quadfacedata:
                f.write(quad)

            print(f"Model {i} exported successfully!\n")

    print("Models exported successfully.")


if __name__ == "__main__":
    print(
        textwrap.dedent(
            f"""\

         Tales of Rebirth / Destiny 2 MDL to Ply converter
         ----------------------------------------------
         By SymphoniaLauren　and Ethanol
         Converts MDL files to ply format for use in conventional 3D modelling software.
         
        """
        )
    )


    if sys.argv[1] == "help":
        print(
            textwrap.dedent(
                f"""\

            Usage:
            py mdltoply.py input output
            py mdltoply.py input output
            """
            )
        )
    else:
        convert()