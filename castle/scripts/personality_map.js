/**
 * Personality Map - v0.1
 * Returns personality-specific responses based on context.
 */

export function getBotResponse(botName, context, botData) {
  const bot = Object.values(botData).find(b => b.name === botName);

  if (!bot) return 'Bot not found.';

  const contextResponses = bot.responses || [];
  if (contextResponses.length === 0) return bot.catchphrase;

  return contextResponses[Math.floor(Math.random() * contextResponses.length)];
}

export function getPersonalityTrait(botId, botData) {
  const bot = botData[botId];
  return {
    name: bot.name,
    personality: bot.personality,
    role: bot.role,
    catchphrase: bot.catchphrase
  };
}

export function matchBotToRoom(botId, roomData, botData) {
  const bot = botData[botId];
  if (roomData.bots_present.includes(botId)) {
    return {
      present: true,
      bot,
      room: roomData.id
    };
  }
  return { present: false };
}
