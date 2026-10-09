/**
 * Castle Engine - v0.1
 * Core logic for room loading, bot interactions, and joke mapping.
 */

export function enterRoom(roomData, botData) {
  console.log(`Entering: ${roomData.name}`);
  console.log(`Description: ${roomData.description}`);

  if (roomData.environment_gags) {
    console.log('\n🏰 Environment:');
    roomData.environment_gags.forEach(gag => console.log(`  - ${gag}`));
  }

  if (roomData.bots_present) {
    console.log('\n🤖 Bots Present:');
    roomData.bots_present.forEach(botId => {
      const bot = botData[botId];
      if (bot) console.log(`  ${bot.name} (${bot.role})`);
    });
  }

  if (roomData.jokes) {
    console.log('\n😄 Jokes:');
    roomData.jokes.forEach(joke => {
      console.log(`  Setup: ${joke.setup}`);
      console.log(`  Punchline: ${joke.punchline}`);
    });
  }

  if (roomData.interactions) {
    console.log('\n✨ Interactions:');
    roomData.interactions.forEach(interaction => console.log(`  → ${interaction}`));
  }
}

export function loadCastle(rooms, bots) {
  return {
    rooms,
    bots,
    enterRoom: (roomId) => enterRoom(rooms[roomId], bots)
  };
}
