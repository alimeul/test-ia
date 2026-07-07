import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import GameStatus from "../components/GameStatus";

afterEach(cleanup);

describe("GameStatus", () => {
  const winPartie = {
    gagne: true,
    termine: true,
    score: 750,
    essais_effectues: 3,
    indices_reveles: 1,
    essais_restants: 2,
    indices_restants: 0,
  };

  const losePartie = {
    gagne: false,
    termine: true,
    score: 0,
    essais_effectues: 5,
    indices_reveles: 2,
    essais_restants: 0,
    indices_restants: 0,
  };

  it("affiche le message de victoire", () => {
    render(<GameStatus partie={winPartie} />);
    expect(screen.getByText("Félicitations !")).toBeTruthy();
    expect(screen.getByText("Score : 750")).toBeTruthy();
  });

  it("affiche le message de défaite", () => {
    render(<GameStatus partie={losePartie} reponse="Paris" />);
    expect(screen.getByText("Perdu !")).toBeTruthy();
    expect(screen.getByText("Paris")).toBeTruthy();
  });

  it("affiche le bouton de partage", () => {
    render(<GameStatus partie={winPartie} />);
    expect(screen.getByText("Partager mon résultat")).toBeTruthy();
  });

  it("construit le texte de partage sans fuite de réponse", () => {
    render(<GameStatus partie={losePartie} reponse="Paris" />);
    const pre = document.querySelector(".share-text");
    expect(pre.textContent).toContain("wikidle.app");
    expect(pre.textContent).not.toContain("Paris");
  });

  it("affiche la grille Wordle pour une victoire", () => {
    render(<GameStatus partie={winPartie} />);
    const pre = document.querySelector(".share-text");
    expect(pre.textContent).toContain("🟩");
    expect(pre.textContent).toContain("⬛");
  });
});
