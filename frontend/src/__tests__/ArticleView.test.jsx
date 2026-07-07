import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import ArticleView from "../components/ArticleView";

describe("ArticleView", () => {
  it("affiche le texte normal", () => {
    const { container } = render(<ArticleView texte="Bonjour le monde" />);
    expect(container.textContent).toContain("Bonjour le monde");
  });

  it("entoure les ██ de balises .mask", () => {
    const { container } = render(<ArticleView texte="█████ est une ville." />);
    const masks = container.querySelectorAll(".mask");
    expect(masks.length).toBe(1);
    expect(masks[0].textContent).toBe("█████");
  });

  it("gère les sauts de paragraphe", () => {
    const { container } = render(<ArticleView texte={"Premier.\n\nSecond."} />);
    const paras = container.querySelectorAll(".article-paragraph");
    expect(paras.length).toBe(2);
    expect(paras[0].textContent).toContain("Premier");
    expect(paras[1].textContent).toContain("Second");
  });

  it("retourne null si pas de texte", () => {
    const { container } = render(<ArticleView texte="" />);
    expect(container.textContent).toBe("");
  });
});
