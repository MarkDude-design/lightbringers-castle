/**
 * Joke Mapper - v0.1
 * Maps jokes to bot personalities and contexts.
 */

export function mapJokesToBots(roomData, botData) {
  const jokes = [];

  if (!roomData.jokes) return jokes;

  roomData.jokes.forEach(joke => {
    const mentionedBots = roomData.bots_present.filter(botId => {
      const bot = botData[botId];
      return joke.punchline.includes(bot.name);
    });

    jokes.push({
      setup: joke.setup,
      punchline: joke.punchline,
      bots_involved: mentionedBots,
      context: roomData.id
    });
  });

  return jokes;
}

export function triggerJoke(joke, botData) {
  console.log(`Setup: ${joke.setup}`);
  console.log(`Punchline: ${joke.punchline}`);

  if (joke.bots_involved.length > 0) {
    console.log('\nBot Reactions:');
    joke.bots_involved.forEach(botId => {
      const bot = botData[botId];
      console.log(`  ${bot.name}: ${bot.responses[0]}`);
    });
  }
}
