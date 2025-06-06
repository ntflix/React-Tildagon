# Reactz (multiplayer)

> A PoC multiplayer game for the [Tildagon](https://tildagon.badge.emfcamp.org/).

A single or multiplayer game where the player waits a random time and then has to react as quickly as possible to a visual cue (like a color change or a button appearing).

The time difference between the event and the player's reaction time is calculated. The lower the time difference, the better the score.

On multiplayer, the player with the lowest time difference wins.

> [!IMPORTANT]  
> `aioespnow` is not included (yet) in Tildagon OS. (There is a PR to get this added to Tildagon OS.)
> In the meantime, install `aioespnow` manually on your Tildagon by running the following command:
>
> ```bash
> mpremote install aioespnow
> ```

## Future

- [x] ~~Have 'game rooms' set up ("would you like to join [randomly generated name] game") so multiple Tildagons in the same vicinity can have separate games~~
- [x] ~~Have a 'game lobby' where players can join and wait for others to join~~
  - ~~A host who can create a game room, start the game etc.~~
- [ ] Have a 'game history' where players can see their previous scores

https://github.com/user-attachments/assets/f87ba258-3989-4452-9a77-2c087711478d
