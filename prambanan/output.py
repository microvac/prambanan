import os

class DirectoryOutputManager(object):
    out = None

    def __init__(self, dir):
        self.last_opened = False
        self.files = []
        self.files_map = {}
        self.dir = dir

    def add(self, filename):
        if not filename in self.files_map:
            base_name = os.path.basename(filename)
            name, ext = os.path.splitext(base_name)
            ext = ".js"
            i = 0
            create_name = lambda x: "%s%s" % (name, ext) if x == 0 else "%s%d%s" % (name, x,ext)
            while create_name(i) in self.files:
                i += 1
            file = create_name(i)
            self.files_map[filename] = file
            self.files.append(file)
        else:
            file = self.files_map[filename]
        return file

    def start(self, filename):
        self.stop()
        file = self.add(filename)
        self.out = open(os.path.join(self.dir, file), "w")

    def stop(self):
        if self.out is not None:
            self.out.close()
            self.out = None

    def is_output_exists(self, filename):
        abs_file = os.path.join(self.dir, self.files_map[filename])
        return os.path.exists(abs_file)


class SingleOutputManager(object):

    def __init__(self, out):
        self.out = out

    def add(self, filename):
        pass

    def start(self, filename):
        self.out.write("\n /*file: %s */ \n" % filename)

    def is_output_exists(self, filename):
        return False

    def stop(self):
        pass
