class EnvManager():
    def __init__(self):
        self.vars = {}
        self.count = 0
        self.fun_scope = {}
        self.fun_scope_counter = 0
        self.fun = {}
        self.label = 0
        self.jz_labels = []
        self.arrays = set()
        self.fun_return = {}
        self.arg_length = None

    def add_var(self, name, typ, offset=1):
        if name is not None:
            self.vars[name] = (self.count, typ)
        prev = self.count
        self.count += offset
        return prev

    def get_var(self, name):
        if name not in self.fun_scope:
            return self.vars[name]
        else:
            return self.fun_scope[name][0]-self.arg_length, self.fun_scope[name][1]

    def var_exists(self, name):
        return name in self.vars or name in self.fun_scope

    def fun_exists(self, name):
        return name in self.fun

    def get_fun_type(self, name):
        return self.fun[name]

    def add_fun(self, name, typ, rtrn):
        self.fun[name] = typ
        self.fun_return[name] = rtrn

    def add_fun_var(self, name, typ):
        self.fun_scope[name] = (self.fun_scope_counter, typ)
        self.fun_scope_counter += 1

    def pop_fun_scope(self):
        self.fun_scope.clear()
        self.fun_scope_counter = 0
        self.arg_length = None

    def new_label(self):
        self.label += 1

    def get_label(self):
        return self.label

    def push_jz_label(self):
        self.jz_labels.append(self.label)
    
    def pop_jz_label(self):
        return self.jz_labels.pop()
    
    def set_array(self, name):
        self.vars[name] = (self.vars[name][0], [self.vars[name][1]])

    def get_fun_return(self, name):
        return self.fun_return[name]

    def set_fun_arg_length(self, size):
        self.arg_length = size



    
