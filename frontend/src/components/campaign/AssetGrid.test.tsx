import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AssetsSchema, DirectionSchema } from "@/lib/schemas";
import { hairCarePackage } from "@/mocks/fixtures/hair-care";
import { AssetGrid } from "./AssetGrid";

const assets = AssetsSchema.parse(hairCarePackage.assets);
const direction = DirectionSchema.parse(hairCarePackage.direction);
const asset = assets.assets[0];
const alt = direction.image_prompts[0];

if (!asset) throw new Error("The hair-care fixture must contain one asset.");

describe("AssetGrid", () => {
  it("renders the image with alt text from the creative direction and an expandable details block", () => {
    render(<AssetGrid assets={assets} direction={direction} />);

    const image = screen.getByRole("img", { name: alt });
    expect(image).toHaveAttribute("src", "/api/assets/hair-care-serum-01.png");

    expect(screen.getByText(asset.prompt)).toBeInTheDocument();
    expect(screen.getByText(asset.model)).toBeInTheDocument();
    expect(screen.getByText(String(asset.seed))).toBeInTheDocument();
    expect(screen.getByText("Details")).toBeInTheDocument();
  });

  it("shows a fallback when the image fails to load", () => {
    render(<AssetGrid assets={assets} direction={direction} />);

    fireEvent.error(screen.getByRole("img", { name: alt }));

    expect(screen.getByText("Image could not be loaded")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: `${alt} (image unavailable)` }),
    ).toBeInTheDocument();
  });

  it("leaves hosted Cloudinary URLs untouched", () => {
    const hosted = AssetsSchema.parse({
      assets: [
        {
          ...asset,
          uri: "https://res.cloudinary.com/demo/image/upload/sample.png",
        },
      ],
    });

    render(<AssetGrid assets={hosted} direction={direction} />);

    expect(screen.getByRole("img", { name: alt })).toHaveAttribute(
      "src",
      "https://res.cloudinary.com/demo/image/upload/sample.png",
    );
  });

  it("shows an empty state when no assets were produced", () => {
    render(<AssetGrid assets={null} direction={null} />);

    expect(screen.getByText("No images produced")).toBeInTheDocument();
  });
});
