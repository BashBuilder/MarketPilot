import type { CampaignPackage } from "@/lib/schemas";

const hairCareScore: NonNullable<CampaignPackage["score"]> = {
  brief_alignment: { score: 9, justification: "Strong fit for the brief and the target audience." },
  audience_fit: { score: 8, justification: "Speaks to busy routines without jargon." },
  copy_quality: { score: 8, justification: "Clear headline and a single, concrete CTA." },
  visual_quality: { score: 7, justification: "Warm still life fits the editorial direction." },
  compliance_risk: { score: 10, justification: "No regulated claims in copy or imagery." },
  total: 84,
};

export const hairCarePackage: CampaignPackage = {
  brief: {
    product: "Lumen & Co. hair-care serum (fictional)",
    goal: "Drive trial sign-ups for a lightweight shine serum",
    audience: "Adults aged 25 to 40 with busy routines",
    tone: "Warm, confident, unfussy",
    channels: ["instagram", "email"], constraints: ["No medical or treatment claims", "No competitor names"],
  },
  research: {
    segments: [
      { name: "Busy professionals", description: "Low-maintenance routines, short on time" },
      { name: "Humidity sufferers", description: "Frizz-prone hair in warm climates" },
    ],
    pain_points: ["Frizz returns by midday", "Heavy products weigh hair down"],
    messaging_angles: ["Effortless shine", "One drop, all day"],
    sources: [
      { title: "Hair-care category report", url: "https://example.com/hair-care-report" },
      { title: "Consumer styling habits", url: "https://example.com/styling-habits" },
    ],
  },
  copy: {
    variants: [
      {
        channel: "instagram",
        headline: "Shine, without the fuss",
        description: "One lightweight drop for all-day gloss, no residue.",
        cta: "Try the serum",
      },
      {
        channel: "email",
        headline: "Your shortcut to everyday shine",
        description: "A fast-absorbing serum that keeps frizz in check.",
        cta: "Claim your sample",
      },
    ],
  },
  direction: {
    style_guide: "Editorial, warm daylight, soft shadows, generous negative space",
    composition: "Bottle centred on warm stone, off-white linen background",
    image_prompts: ["A matte serum bottle on warm stone, morning light, editorial still life"],
    video_prompts: ["Slow push-in on the bottle as light shifts across the label"], negative_prompts: ["text overlays", "harsh flash", "cluttered background"],
  },
  assets: {
    assets: [
      {
        uri: "hair-care-serum-01.png",
        checksum: "3f786850e387550fdab836ed7e6dc881de23001b1e8bd3fca05f8a61b6f3e9c1",
        model: "fake-image-v1",
        seed: 42,
        prompt: "A matte serum bottle on warm stone, morning light, editorial still life",
      },
    ],
  },
  compliance: {
    items: [
      { check: "No medical claims", passed: true, reason: "Copy avoids treatment language." },
      { check: "No unverifiable claims", passed: true, reason: "Only sensory, observable claims." },
      { check: "No competitor references", passed: true, reason: "No other brands are named." },
    ],
  },
  score: hairCareScore,
};

export const hairCareRevision: CampaignPackage = {
  ...hairCarePackage,
  copy: {
    variants: [
      {
        channel: "instagram",
        headline: "All-day shine, one drop",
        description: "A weightless serum that tames frizz from morning to night.",
        cta: "Try the serum",
      },
      {
        channel: "email",
        headline: "Shine that lasts past lunch",
        description: "Fast-absorbing, never heavy. Meet your new daily finish.",
        cta: "Claim your sample",
      },
    ],
  },
  score: {
    ...hairCareScore,
    copy_quality: { score: 9, justification: "Tighter headlines with a clearer promise." },
    total: 88,
  },
};
