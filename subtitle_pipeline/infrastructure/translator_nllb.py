"""Adapter dich da ngon ngu bang NLLB-200 (distilled 600M) qua thu vien
transformers. Import thu vien nang chi trong __enter__/translate, khong o
top-level, giong cac adapter khac (xem docs/CODE_STYLE.md).

CANH BAO RUI RO CAO HON CAC ADAPTER KHAC: day la adapter DUY NHAT chua tung
duoc chay/kiem thu du mot lan nao (kha ca faster-whisper/whisperx/pyannote it
nhat da dua tren API quen thuoc, con cach goi NLLB qua tokenizer.generate() o
day chi dua theo tai lieu HuggingFace, CHUA verify tren may that). Cac diem co
the sai: ten tham so co the doi giua cac phien ban `transformers`, hoac
`forced_bos_token_id` can lay tu `tokenizer.lang_code_to_id` thay vi
`convert_tokens_to_ids` tuy phien ban. Xem HANDOFF.md Phase 5 truoc khi tin
tuong ket qua dich.
"""
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.infrastructure.gpu import release_gpu_memory

# NLLB dung ma ngon ngu rieng (vd. "vie_Latn" cho tieng Viet), khac voi ma ISO
# 639-1 ngan gon dung o cac buoc khac cua pipeline (vd. "vi").
NLLB_LANGUAGE_CODES = {
    "vi": "vie_Latn",
    "en": "eng_Latn",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "fr": "fra_Latn",
    "es": "spa_Latn",
}

# Danh sach ngon ngu dich/long tieng dung chung cho ca Upload va Editor page -
# dat o day (thay vi hardcode rieng tung noi) vi day la nguon gioi han thuc su
# (phai ho tro ca NLLB lan edge-tts, xem infrastructure/tts_edge.py).
SUPPORTED_LANGUAGES = list(NLLB_LANGUAGE_CODES.keys())


class NLLBTranslator:
    def __init__(
        self,
        source_language: str,
        target_language: str,
        device: str,
        model_name: str = "facebook/nllb-200-distilled-600M",
    ):
        if source_language not in NLLB_LANGUAGE_CODES:
            raise ValueError(f"Ngon ngu nguon chua ho tro: {source_language}")
        if target_language not in NLLB_LANGUAGE_CODES:
            raise ValueError(f"Ngon ngu dich chua ho tro: {target_language}")
        self._source_code = NLLB_LANGUAGE_CODES[source_language]
        self._target_code = NLLB_LANGUAGE_CODES[target_language]
        self._device = device
        self._model_name = model_name
        self._tokenizer = None
        self._model = None

    def __enter__(self) -> "NLLBTranslator":
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_name, src_lang=self._source_code
        )
        self._model = AutoModelForSeq2SeqLM.from_pretrained(self._model_name)
        if self._device == "cuda":
            import torch

            self._model = self._model.to(torch.device("cuda"))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._tokenizer = None
        self._model = None
        release_gpu_memory()

    def translate(self, segments: list[SubtitleSegment]) -> list[SubtitleSegment]:
        target_token_id = self._tokenizer.convert_tokens_to_ids(self._target_code)
        translated = []
        for seg in segments:
            inputs = self._tokenizer(seg.text, return_tensors="pt")
            if self._device == "cuda":
                inputs = {key: value.to("cuda") for key, value in inputs.items()}
            output_tokens = self._model.generate(
                **inputs, forced_bos_token_id=target_token_id, max_length=256
            )
            text = self._tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0]
            translated.append(
                SubtitleSegment(start=seg.start, end=seg.end, text=text, speaker=seg.speaker)
            )
        return translated
