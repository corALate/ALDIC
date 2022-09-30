import re

from ..util.printer import cons

from . import engines
from . import input

from ..util import common

from .. import build


class MFCRun:
    def __init__(self, mfc):
        self.mfc = mfc

    def validate_job_options(self) -> None:
        if self.mfc.args["cpus_per_node"] != self.mfc.args["gpus_per_node"] \
            and self.mfc.args["gpus_per_node"] != 0:
            raise common.MFCException("RUN: Conflicting job execution parameters. If using GPUs, CPUs per node and GPUs per node must match.")

        if self.mfc.args["nodes"] <= 0:
            raise common.MFCException("RUN: At least one node must be requested.")

        if self.mfc.args["cpus_per_node"] <= 0:
            raise common.MFCException("RUN: At least one CPU per node must be requested.")

        if not common.isspace(self.mfc.args["email"]):
            # https://stackoverflow.com/questions/8022530/how-to-check-for-valid-email-address
            if not re.match(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?", self.mfc.args["email"]):
                raise common.MFCException(f'RUN: {self.mfc.args["email"]} is not a valid e-mail address.')

        engines.get_engine(self.mfc.args["engine"]).validate_job_options(self.mfc)

    def run(self) -> None:
        cons.print("[bold]Run[/bold]")
        cons.indent()

        if len(self.mfc.args["targets"]) == 0:
            cons.print(f"> No target selected.")
            return

        input_file = input.load(self.mfc.args)

        engine = engines.get_engine(self.mfc.args["engine"])
        engine.init(self.mfc, input_file)

        cons.print(f"Configuration:")
        cons.indent()
        cons.print(f"""\
Input               {self.mfc.args['input']}
Job Name      (-#)  {self.mfc.args['name']}
Engine        (-e)  {self.mfc.args['engine']}
{engine.get_args()}\
""")
        cons.unindent()

        self.validate_job_options()

        for target_name in self.mfc.args["targets"]:
            cons.print(no_indent=True)
            cons.print(f"[bold]Running [magenta]{target_name}[/magenta][/bold]:")
            cons.indent()

            # We generate the /path/to/case/{target_name}.inp and
            # src/{target_name}/case.fpp input files before building so that, in
            # order for the target to be built with case optimization, if
            # args["case_optimization"] is true. Doing so later, would require
            # there be two builds of a target.
            input_file.generate(target_name)

            if not self.mfc.args["no_build"]:
                build.build_target(self.mfc, target_name)

            engine.run(target_name)

            cons.unindent()

        cons.unindent()
