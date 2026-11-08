export interface ExamplePrompt {
  label: string;
  idea: string;
}

export const EXAMPLE_PROMPTS: readonly ExamplePrompt[] = [
  {
    label: "Hair care",
    idea: "Create an advertising campaign for a fictional hair-care product targeting adults aged 25 to 40.",
  },
  {
    label: "Cold brew",
    idea: "Create an advertising campaign for a small-batch cold brew coffee brand targeting commuters aged 22 to 35.",
  },
  {
    label: "Running shoes",
    idea: "Create an advertising campaign for a sustainable running shoe made from recycled materials, targeting first-time marathon runners.",
  },
];
