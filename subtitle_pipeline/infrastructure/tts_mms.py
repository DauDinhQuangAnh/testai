"""Adapter text-to-speech dung MMS-TTS (Meta Massively Multilingual Speech)
qua thu vien transformers. Chon MMS-TTS thay vi Coqui XTTS-v2 (voice cloning
tot hon) vi XTTS-v2 KHONG co checkpoint tieng Viet trong 17 ngon ngu ho tro -
trong khi MMS-TTS co checkpoint rieng cho ~1100 ngon ngu, bao gom
`facebook/mms-tts-vie`. Doi lai, MMS-TTS la VITS single-speaker, KHONG ho tro
voice cloning (chap nhan duoc - xem HANDOFF.md Phase 5b, quyet dinh nguoi dung
chon giong doc chuan thay vi clone giong goc cho ban v1).

CANH BAO RUI RO (cung muc do voi translator_nllb.py): day la adapter TTS DUY
NHAT, CHUA TUNG duoc chay/kiem thu. Cach goi VitsTokenizer/VitsModel chi dua
theo tai lieu HuggingFace, chua verify tren may that. Xem HANDOFF.md Phase 5b
truoc khi tin tuong ket qua audio sinh ra.
"""
from pathlib import Path

from subtitle_pipeline.infrastructure.gpu import release_gpu_memory

# MMS-TTS dung ma ISO 639-3 rieng cho ten checkpoint HuggingFace
# (vd. "facebook/mms-tts-vie"), khac voi ma ISO 639-1 ngan gon dung o cac buoc
# khac cua pipeline (vd. "vi"). Chi liet ke cac ngon ngu pipeline nay da ho tro
# o buoc dich (xem translator_nllb.NLLB_LANGUAGE_CODES) - MMS-TTS co checkpoint
# cho nhieu ngon ngu hon nhieu, them vao day khi can.
MMS_LANGUAGE_CODES = {
    "vi": "vie",
    "en": "eng",
    "zh": "cmn",
    "ja": "jpn",
    "ko": "kor",
    "fr": "fra",
    "es": "spa",
}


class MMSTTSSynthesizer:
    def __init__(self, language: str, device: str):
        if language not in MMS_LANGUAGE_CODES:
            raise ValueError(f"Ngon ngu TTS chua ho tro: {language}")
        self._language_code = MMS_LANGUAGE_CODES[language]
        self._device = device
        self._model_name = f"facebook/mms-tts-{self._language_code}"
        self._tokenizer = None
        self._model = None

    def __enter__(self) -> "MMSTTSSynthesizer":
        from transformers import VitsModel, VitsTokenizer

        self._tokenizer = VitsTokenizer.from_pretrained(self._model_name)
        self._model = VitsModel.from_pretrained(self._model_name)
        if self._device == "cuda":
            import torch

            self._model = self._model.to(torch.device("cuda"))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._tokenizer = None
        self._model = None
        release_gpu_memory()

    @property
    def sample_rate(self) -> int:
        return self._model.config.sampling_rate

    def synthesize(self, text: str, output_path: Path) -> None:
        import soundfile as sf
        import torch

        inputs = self._tokenizer(text, return_tensors="pt")
        if self._device == "cuda":
            inputs = {key: value.to("cuda") for key, value in inputs.items()}
        with torch.no_grad():
            output = self._model(**inputs)
        waveform = output.waveform[0].cpu().numpy()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), waveform, self._model.config.sampling_rate)
