"""Divisão de transcrições em blocos; sem dependências de banco."""


def chunk_segments(
    segments: list,
    max_words: int = 150,
    overlap_words: int = 30,
) -> list:
    """
    Agrupa segmentos do Whisper em janelas de contexto,
    preservando timestamps e sobreposição de palavras.
    """
    chunks = []
    current_chunk_words = []
    current_start = None
    current_end = None

    for seg in segments:
        text = seg.get("text", "").strip()

        if not text:
            continue

        words = text.split()

        if current_start is None:
            current_start = float(
                seg.get("start", 0.0)
            )

        current_end = float(
            seg.get("end", 0.0)
        )

        current_chunk_words.extend(words)

        if len(current_chunk_words) >= max_words:
            chunks.append({
                "text": " ".join(current_chunk_words),
                "start": current_start,
                "end": current_end,
            })

            overlap_text = (
                current_chunk_words[-overlap_words:]
                if len(current_chunk_words) > overlap_words
                else []
            )

            current_chunk_words = overlap_text
            current_start = current_end

    if current_chunk_words:
        chunks.append({
            "text": " ".join(current_chunk_words),
            "start": current_start,
            "end": current_end,
        })

    return chunks
