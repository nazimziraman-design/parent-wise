"""Local photoreal image generation on the GPU (SDXL Lightning, 4-6 steps). Free, offline after the first download.
Usage: python imagegen.py <out.jpg> "<prompt>" [--w 1024] [--h 1024] [--seed 7]
Prompts are for ordinary, dignified, fully clothed people/scenes; the negative prompt blocks text, logos and unsafe content."""
import argparse, os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path(__file__).parent / ".models"))
import torch
from diffusers import EulerAncestralDiscreteScheduler, StableDiffusionXLPipeline

REPO = "SG161222/RealVisXL_V5.0_Lightning"
NEG = ("text, letters, watermark, logo, signature, cartoon, 3d render, illustration, deformed, distorted face, extra fingers, "
       "bad hands, blurry, low quality, nsfw, nude, naked, bare skin, violence, blood, injury, sad crying")


def load():
    try:
        pipe = StableDiffusionXLPipeline.from_pretrained(REPO, torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
    except Exception:  # noqa: BLE001
        pipe = StableDiffusionXLPipeline.from_pretrained(REPO, torch_dtype=torch.float16, use_safetensors=True)
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_slicing()
    return pipe


def generate(pipe, prompt, out, w=1024, h=1024, seed=7):
    g = torch.Generator("cpu").manual_seed(seed)
    img = pipe(prompt + ", fully clothed, natural skin, photorealistic, sharp focus, no text", negative_prompt=NEG, width=w, height=h,
               num_inference_steps=6, guidance_scale=1.5, generator=g).images[0]
    img.save(out, quality=93)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("prompt")
    ap.add_argument("--w", type=int, default=1024); ap.add_argument("--h", type=int, default=1024); ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    generate(load(), a.prompt, a.out, a.w, a.h, a.seed)
    print("ok", a.out)
