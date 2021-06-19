from hitchrunpy import HitchRunPyException
from hitchstory import BaseEngine, GivenDefinition, GivenProperty
from hitchstory import no_stacktrace_for, validate
from strictyaml import Map, MapPattern, Optional, Str, Int
from templex import Templex
import time


class Engine(BaseEngine):
    given_definition = GivenDefinition(
        python_version=GivenProperty(Str()),
        setup=GivenProperty(Str()),
        files=GivenProperty(MapPattern(Str(), Str())),
    )

    def __init__(self, build, rewrite=False, cprofile=False):
        self._build = build
        self._rewrite = rewrite
        self._cprofile = cprofile

    def set_up(self):
        self._build.ensure_built()

        for filename, contents in self.given.get("files", {}).items():
            filepath = self._build.working.parent.joinpath(filename)
            if not filepath.dirname().exists():
                filepath.dirname().makedirs()
            filepath.write_text(contents)

    def assert_text(self, will_output, actual_output):
        Templex(will_output).assert_match(actual_output)

    def _story_friendly_output(self, text):
        return text

    @no_stacktrace_for(AssertionError)
    @no_stacktrace_for(HitchRunPyException)
    @validate(
        code=Str(),
        will_output=Str(),
        environment_vars=MapPattern(Str(), Str()),
        raises=Map({Optional("type"): Str(), Optional("message"): Str()}),
    )
    def run(self, code, will_output=None, environment_vars=None, raises=None):
        self.example_py_code = (
            self._build.example_python_code.with_terminal_size(160, 100)
            .with_env(**{} if environment_vars is None else environment_vars)
            .with_setup_code(self.given.get("setup", ""))
        )

        to_run = self.example_py_code.with_code(code)

        if self._cprofile:
            to_run = to_run.with_cprofile(
                self.path.profile.joinpath("{0}.dat".format(self.story.slug))
            )

        result = (
            to_run.expect_exceptions().run() if raises is not None else to_run.run()
        )

        actual_output = self._story_friendly_output(result.output)

        if will_output is not None:
            try:
                self.assert_text(will_output, actual_output)
            except AssertionError:
                if self._rewrite:
                    self.current_step.update(**{"will output": actual_output})
                else:
                    raise

        if raises is not None:
            exception_type = raises.get("type")
            message = raises.get("message")

            try:
                result.exception_was_raised(exception_type)
                exception_message = self._story_friendly_output(
                    result.exception.message
                )
                self.assert_text(exception_message, message)
            except AssertionError:
                if self._rewrite:
                    new_raises = raises.copy()
                    new_raises["message"] = exception_message
                    self.current_step.update(raises=new_raises)
                else:
                    raise

    @validate(seconds=Int())
    def sleep(self, seconds):
        time.sleep(int(seconds))

    def on_success(self):
        if self._rewrite:
            self.new_story.save()
