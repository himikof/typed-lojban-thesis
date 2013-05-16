from waflib import TaskGen, Task, Utils
from itertools import tee, ifilterfalse, ifilter

def configure(conf):
    conf.find_program('pandoc')
    conf.find_program('lhs2TeX')

class pandoc(Task.Task):
    run_str = '${PANDOC} -r ${PFORMAT_READ} -w ${PFORMAT_WRITE} ' \
            '${PFLAGS} -o ${TGT} ${SRC}'
    color = 'PINK'
    shell = False

class lhs2tex(Task.Task):
    run_str = '${LHS2TEX} ${LHSFLAGS} -o ${TGT} ${SRC}'
    color = 'BLUE'
    shell = False

class lhs_preamble(Task.Task):
    run_str = 'echo %%include polycode.fmt > ${TGT[0]}'
    color = 'BLUE'
    shell = True

@TaskGen.taskgen_method
@TaskGen.before('process_source')
@TaskGen.feature('pandoc', 'pandoc-merge')
def apply_read_format_extensions(self):
    disabled_exts = Utils.to_list(getattr(self, 'disable_exts', []))
    read_format = getattr(self, 'read_format', 'markdown')
    read_format += ''.join(('-' + e for e in disabled_exts))
    self.read_format = read_format

def partition(pred, iterable):
    'Use a predicate to partition entries into false entries and true entries'
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return ifilterfalse(pred, t1), ifilter(pred, t2)

@TaskGen.taskgen_method
@TaskGen.feature('pandoc', 'pandoc-merge')
@TaskGen.before_method('process_source')
def apply_bib(self):
    self.source, bibs = partition(lambda node: node.name.endswith('.bib'),
                                  self.to_nodes(self.source))
    self.__dict__.setdefault('dep_nodes', [])
    if bibs:
        self.env.append_value('PFLAGS', '--natbib')
    for bib in bibs:
        path = bib.path_from(self.bld.bldnode)
        self.env.append_value('PFLAGS', '--bibliography=' + path)
        self.dep_nodes.append(bib)

@TaskGen.extension('.pd')
def process_pandoc(self, node):
    out_source = node.change_ext('.latex', '.pd')
    tsk = self.create_task('pandoc', [node], out_source)
    tsk.env.append_value('PFLAGS', Utils.to_list(getattr(self, 'flags', [])))
    tsk.env['PFORMAT_READ'] = getattr(self, 'read_format', 'markdown')
    tsk.env['PFORMAT_WRITE'] = getattr(self, 'write_format', 'latex')
    tsk.dep_nodes += getattr(self, 'dep_nodes', [])
    self.__dict__.setdefault('compiled_src', [])
    self.compiled_src.extend(tsk.outputs)

@TaskGen.extension('.pdlhs')
def process_pandoc(self, node):
    lhs_source = node.change_ext('.lhs', '.pdlhs')
    lhs_preamble = self.bld.bldnode.find_or_declare('lhs-preable.lhs')
    self.create_task('lhs_preamble', [], lhs_preamble)
    tsk = self.create_task('pandoc', [node], lhs_source)
    tsk.env.append_value('PFLAGS', Utils.to_list(getattr(self, 'flags', [])))
    tsk.env['PFORMAT_READ'] = getattr(self, 'read_format', 'markdown') + '+lhs'
    tsk.env['PFORMAT_WRITE'] = getattr(self, 'write_format', 'latex')
    tsk.dep_nodes += getattr(self, 'dep_nodes', [])
    #out_source = lhs_source.change_ext('.latex', '.lhs')
    #tsk2 = self.create_task('lhs2tex', [lhs_source], out_source)
    #tsk2.env.append_value('LHSFLAGS', '--include=' + lhs_preamble.path_from(self.bld.bldnode))
    #tsk2.dep_nodes.append(lhs_preamble)
    self.__dict__.setdefault('compiled_src', [])
    self.compiled_src.extend(tsk.outputs)

@TaskGen.extension('.latex')
def process_latex(self, node):
    self.__dict__.setdefault('compiled_src', [])
    self.compiled_src.append(node)

@TaskGen.taskgen_method
@TaskGen.feature('pandoc-merge')
@TaskGen.after_method('process_source')
def apply_link(self):
    tsk = self.create_task('pandoc', self.compiled_src)
    format = getattr(self, 'write_format', 'latex')
    tsk.env['PFORMAT_READ'] = format
    tsk.env['PFORMAT_WRITE'] = format
    tsk.env['PFLAGS'] = Utils.to_list(getattr(self, 'linkflags', []))
    if getattr(self, 'template', None):
        template = self.to_nodes(self.template)[0]
        path = template.path_from(self.bld.bldnode)
        tsk.env.append_value('PFLAGS', "--template={0}".format(path))
        tsk.dep_nodes.append(template)
    if getattr(self, 'target', None):
        self.target = Utils.to_list(self.target)
        for x in self.target:
            if isinstance(x, str):
                tsk.outputs.append(self.path.find_or_declare(x))
            else:
                x.parent.mkdir()
                tsk.outputs.append(x)
        if getattr(self,'install_path',None):
            self.bld.install_files(self.install_path, tsk.outputs)

