function ArticleView({ texte }) {
  if (!texte) return null;

  const paragraphs = texte.split("\n").filter(Boolean);

  return (
    <section className="article-view">
      {paragraphs.map((p, i) => (
        <p key={i} className="article-paragraph">
          {p.split(/(█+)/).map((part, j) =>
            part.startsWith("█") ? (
              <span key={j} className="mask" aria-label="mot masqué">
                {part}
              </span>
            ) : (
              <span key={j}>{part}</span>
            )
          )}
        </p>
      ))}
    </section>
  );
}

export default ArticleView;
