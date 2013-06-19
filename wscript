# vim: set filetype=python :

import os.path
from waflib import TaskGen, Task, Utils

def configure(conf):
    conf.load('tex')
    conf.load('pandoc', tooldir='.')

def build(bld):
    sources = """
        Introduction.pd
        ch_01/chapter.latex
        ch_01/LojbanIntro.pd
        ch_01/FormalGrammars.pd
        ch_02/chapter.latex
        ch_02/Typing.pd
        ch_02/FormalLojban.pd
        ch_02/TypingInHaskell.pd
        ch_03/chapter.latex
        ch_03/ImplDescription.pd
        ch_03/Implementation.pdlhs
        Conclusion.pd
    """
    bld(features='pandoc-merge', source=sources + ' bib.bib', target='main.latex',
            disabled_exts='fancy_lists', write_format='latex+lhs',
            flags='-R -S --latex-engine=xelatex --listings --no-highlight --chapters',
            linkflags='--toc --chapters --no-highlight -R', template='template.latex')

    # Outputs main.pdf
    bld(features='tex', type='xelatex', source='main.latex', prompt=True)
    bld.add_manual_dependency(bld.bldnode.find_or_declare('main.pdf'),
                              bld.srcnode.find_node('utf8gost705u.bst'))
