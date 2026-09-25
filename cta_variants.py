"""Rotating wording for the comment CTA. Variants are deliberately close to each other; studio picks the least/oldest used one per post.
Edit freely (keep {KW} / {stage} placeholders; never use: free, guide, ebook, cheat sheet, PDF, download, bundle).
When the Gumroad products exist, change the product wording here (e.g. add product names) in one place."""

INTROS = [  # stage guides; {stage} = age range such as "2-4"
    "If you’re in the {stage} stage right now and every day feels like a new challenge,",
    "If you’re in the middle of the {stage} stage and every day feels like a test,",
    "If the {stage} stage is testing you right now,",
    "If you’re living the {stage} stage right now and some days feel too long,",
    "If you’re deep in the {stage} stage and every day brings something new,",
]
OFFERS = [
    "The ParentWise Playbook puts decades of research in one place, with simple scripts, regulation tools and real-life support for the moments that test you most.",
    "Inside the ParentWise Playbook: decades of research turned into simple scripts, calming tools and real-life support for the moments that test you most.",
    "The ParentWise Playbook brings decades of research together in one place, with easy scripts, regulation tools and practical support for the hardest moments.",
    "Everything in this post, and more, lives in the ParentWise Playbook: research-based scripts, regulation tools and real-life support for the moments that test you most.",
    "The ParentWise Playbook gathers decades of research into one place, with ready-to-use scripts, calming tools and real-life support for the days that feel too hard.",
]
COMMENTS = [
    "Comment {KW} and I’ll send you the link.",
    "Comment {KW} below and I’ll send you the link.",
    "Just comment {KW} and I’ll send you the link.",
    "Type {KW} in the comments and I’ll send you the link.",
    "Comment {KW} and I’ll send the link straight to you.",
]
FOOTS = [
    "Save · Share · Follow / Subscribe",
    "Save it · Share it · Follow / Subscribe",
    "Save this · Share it · Follow / Subscribe",
]
POOLS = {"intro": INTROS, "offer": OFFERS, "comment": COMMENTS, "foot": FOOTS}


STEPS = {"intro": (2, 0), "offer": (3, 0), "comment": (4, 0), "foot": (1, 1)}  # (stride, offset): each pool walks in a different order


def pick(history):
    """history = variant dicts of earlier posts, oldest first. Least-used index per pool; ties go to the longest unused, then the pool's own walk order."""
    out = {}
    for key, pool in POOLS.items():
        n = len(pool)
        stride, off = STEPS[key]
        walk = [(k * stride + off) % n for k in range(n)]
        used = [h.get(key) for h in history if h.get(key) is not None]
        def score(i):
            last = max([m for m, u in enumerate(used) if u == i], default=-1)
            return (used.count(i), last, walk.index(i))
        out[key] = min(range(n), key=score)
    return out
