/**
 * Q Switch - v0.1
 * Applies Q overlay with cosmic commentary.
 */

export function applyQOverlay(text) {
  const qComments = [
    "Only God can judge me… but I can comment.",
    "Base-three invocation detected. Avalanche mode engaged.",
    "The universe expands because it fears your playlist."
  ];

  const randomComment = qComments[Math.floor(Math.random() * qComments.length)];
  return `${text}\n\n[Q Overlay]: ${randomComment}`;
}

export function addMakaveliAdjacency(text) {
  const makaveliFilters = [
    text.toUpperCase(),
    `*${text}*`,
    `⚡ ${text} ⚡`
  ];
  return makaveliFilters[Math.floor(Math.random() * makaveliFilters.length)];
}

export function addAvalancheEnergy(text) {
  return `${text}\n💥 AVALANCHE MODE ENGAGED`;
}
