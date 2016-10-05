import shutil
from datetime import datetime
from pathlib import Path


class SassGenerator:
    _errors, _files_generated = 0, 0
    _outdir_src = None

    def __init__(self, input_dir: str, output_dir: str, debug: bool=False):
        try:
            import sass
        except ImportError as e:
            raise RuntimeError('Could not import sass, you might need to run "pip install libsass"') from e
        self._sass = sass
        self._in_dir = Path(input_dir).resolve()
        assert self._in_dir.is_dir()
        self._out_dir = Path(output_dir)
        self._debug = debug
        if self._debug:
            self._out_dir_src = self._out_dir / '.src'
            self._src_dir = self._out_dir_src
        else:
            self._src_dir = self._in_dir

    def build(self):
        start = datetime.now()
        self._errors, self._files_generated = 0, 0
        if self._out_dir.exists():
            shutil.rmtree(str(self._out_dir.resolve()))

        if self._debug:
            self._out_dir.mkdir(parents=True)
            # shutil.copytree(str(self._in_dir.resolve()), str(self._out_dir_src))
            self._out_dir_src.symlink_to(self._in_dir.resolve(), target_is_directory=True)

        self.process_directory(self._src_dir)
        time_taken = (datetime.now() - start).total_seconds() * 1000
        print('%d css files generated in %0.0fms, %d errors' % (self._files_generated, time_taken, self._errors))

    def process_directory(self, d: Path):
        assert d.is_dir()
        for p in d.iterdir():
            if p.is_dir():
                self.process_directory(p)
            elif p.is_file():
                self.process_file(p)

    def process_file(self, f: Path):
        if f.suffix not in {'.css', '.scss', '.sass'}:
            return

        rel_path = f.relative_to(self._src_dir)
        css_path = (self._out_dir / rel_path).with_suffix('.css')

        map_path, output_style = None, 'compressed'
        if self._debug:
            map_path = css_path.with_suffix('.map')

        if f.name.startswith('_'):
            # mixin, not copied
            return

        print('    %s ▶ %s' % (rel_path, css_path.relative_to(self._out_dir)))
        try:
            css = self._sass.compile(
                filename=str(f),
                source_map_filename=str(map_path),
                output_style=output_style,
                precision=10,
            )
        except self._sass.CompileError as e:
            self._errors += 1
            print('"{}", compile error: {}'.format(f, e))
            return

        css_path.parent.mkdir(parents=True, exist_ok=True)
        if self._debug:
            css, css_map = css
            map_path.write_text(css_map)
        css_path.write_text(css)
        self._files_generated += 1
