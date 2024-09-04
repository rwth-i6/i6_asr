__all__ = ["ApplySentencePieceJob"]


from enum import Enum
import logging
import subprocess

from sisyphus import *

from i6_core.util import uopen

try:
    import sentencepiece
except ImportError:
    if not hasattr(gs, "WARNING_NO_SENTENCEPIECE") or gs.WARNING_NO_SENTENCEPIECE is True:
        logging.warning(
            "The package 'sentencepiece' is not installed in the manager python env. Please make sure it is installed "
            "in the python environment running the Sisyphus worker. To suppress this warning set "
            "'WARNING_NO_SENTENCEPIECE=False' in the settings.py"
        )


class SentencePieceType(Enum):
    UNIGRAM = "unigram"
    BPE = "bpe"
    CHAR = "char"
    WORD = "word"


class ApplySentencePieceJob(Job):
    """
    Apply the sentence-piece model to a text file

    See also `https://github.com/google/sentencepiece`_
    """

    def __init__(
        self,
        text_file,
        model,
        extra_options=None,
    ):
        """

        :param tk.Path text_file: raw text or gzipped text to be converted
        :param tk.Path model: SPM model
        :param tk.Path extra_options: Extra arguments for the SentencePiece library
        :param dict|None additional_options: additional trainer options, see `https://github.com/google/sentencepiece/blob/master/doc/options.md`_
        """

        self.text_file = text_file
        self.model = model
        self.extra_options = extra_options or {}

        self.out_text = self.output_path("processed.text.gz")

        self.rqmt = {"cpu": 1, "mem": 2, "time": 4}

    def tasks(self):
        yield Task("run", rqmt=self.rqmt)

    def run(self):
        import sentencepiece

        text_path = self.text_file.get_path()
        if text_path.endswith(".gz"):
            local_text_path = "unzipped_text.txt"
            outfile = open(local_text_path, "wt")
            subprocess.check_call(["gzip", "-dc", text_path], stdout=outfile)
            text_path = local_text_path

        sp_ctrl = sentencepiece.SentencePieceProcessor()
        sp_ctrl.load(self.model.get_path())

        with uopen(text_path, "rt") as in_text, uopen(self.out_text, "wt") as out_text:
            for sentence in in_text:
                out_text.write(" ".join(sp_ctrl.encode_as_pieces(sentence)) + "\n")
