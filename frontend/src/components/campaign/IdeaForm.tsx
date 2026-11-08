"use client";

import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { MAX_IDEA_LENGTH } from "@/lib/schemas";
import { EXAMPLE_PROMPTS } from "./example-prompts";

export interface IdeaFormProps {
  onSubmit: (idea: string) => void | Promise<void>;
}

function validateIdea(idea: string): string | null {
  const trimmed = idea.trim();
  if (!trimmed) return "Enter a campaign idea before creating it.";
  if (trimmed.length > MAX_IDEA_LENGTH) {
    return `Keep the idea to ${MAX_IDEA_LENGTH} characters or fewer.`;
  }
  return null;
}

export function IdeaForm({ onSubmit }: IdeaFormProps) {
  const [idea, setIdea] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;

    const nextError = validateIdea(idea);
    if (nextError) {
      setError(nextError);
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit(idea.trim());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not create the campaign.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  function chooseExample(prompt: string) {
    setIdea(prompt);
    setError(null);
    textareaRef.current?.focus();
  }

  const describedBy = error
    ? "campaign-idea-counter campaign-idea-error"
    : "campaign-idea-counter";

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FieldGroup>
        <Field data-invalid={error ? true : undefined}>
          <FieldLabel htmlFor="campaign-idea">Campaign idea</FieldLabel>
          <Textarea
            id="campaign-idea"
            ref={textareaRef}
            value={idea}
            onChange={(event) => {
              setIdea(event.target.value);
              if (error) setError(null);
            }}
            onKeyDown={handleKeyDown}
            maxLength={MAX_IDEA_LENGTH}
            rows={6}
            disabled={isSubmitting}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            placeholder="Describe the product, audience and goal for the campaign."
          />
          <div className="flex flex-wrap items-start justify-between gap-2">
            <FieldDescription id="campaign-idea-counter">
              {idea.length} / {MAX_IDEA_LENGTH} characters
            </FieldDescription>
            {error ? <FieldError id="campaign-idea-error">{error}</FieldError> : null}
          </div>
        </Field>

        <div>
          <p className="text-sm font-medium text-foreground">Try an example</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <Button
                key={prompt.label}
                type="button"
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() => chooseExample(prompt.idea)}
              >
                {prompt.label}
              </Button>
            ))}
          </div>
        </div>
      </FieldGroup>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-small text-muted-foreground">
          Press Ctrl+Enter or Cmd+Enter to submit.
        </p>
        <Button type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
          {isSubmitting ? "Creating campaign…" : "Create campaign"}
        </Button>
      </div>
    </form>
  );
}
