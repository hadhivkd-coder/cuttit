"""Per-style editing instructions for Claude. Add a style here to support it in the planner."""

STYLES: dict[str, str] = {
    "talking_head": """Style: talking-head reel for Instagram/WhatsApp (9:16, aim for 30-90 seconds).
- Open with the strongest line: a hook, a bold claim or a question. Move it to the front if it was said later.
- Remove filler words, false starts, repeated takes (keep the best take, usually the last one), and dead air.
- Keep the message complete and in a logical order; never cut mid-sentence.
- If the speaker clearly says something like "cut this" or "start again", drop that part.
- End on a clear closing line or call to action if there is one.""",

    "podcast": """Style: podcast clip (9:16, aim for 45-120 seconds).
- Find the single most interesting, self-contained moment: a story, an insight, or a strong opinion.
- Start right where that moment starts; it must make sense without the earlier conversation.
- Keep natural back-and-forth between speakers, but remove long pauses, filler and off-topic tangents.
- End when the point lands; don't trail off.""",
}

NOT_READY = {"real_estate", "product", "event"}


def instructions(style: str) -> str:
    if style in STYLES:
        return STYLES[style]
    if style in NOT_READY:
        raise NotImplementedError(f"style '{style}' is not automated yet; edit it by hand for now")
    raise ValueError(f"unknown style '{style}'")
