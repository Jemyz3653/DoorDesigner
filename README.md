# Door Designer 1.0.0

Choose door cutouts independently from wood and paint color.

Craft the Door Chisel from a copper ingot and an iron nugget. Use it on a placed wooden door or trapdoor to convert it. Further clicks cycle four cutout designs. Sneak to cycle backwards. All 13 vanilla wood types are available. Use a dye on a designed door or trapdoor to paint it. Converting a ColoredM wooden door or trapdoor keeps its dye color. Both door halves update together. Facing, hinge, open state, powered state and trapdoor waterlogging are retained. Breaking returns an item with its selected cutout and color. Original pixel wood textures are included.

## Installation

Minecraft Java 26.3, Java 25, Fabric Loader 0.19.5 or later, and Fabric API 0.163.0+26.3 or later. For singleplayer, install the JAR and Fabric API on the client. For multiplayer, install matching versions on the server and every client.

English and Russian translations are included. Build with JDK 25 using `bash gradlew build` or `gradlew.bat build`.

Made by AI ChatGPT - By OpenAI.

## Source layout

All 3,537 PNG textures are stored losslessly in `texture-sources.zip` at their normal `assets/doordesigner/textures/...` paths. Gradle unpacks them automatically during `processResources`; no manual extraction is required. The complete source archive attached to the GitHub release also includes the original individual PNG files. The published gameplay JAR is unchanged and matches the approved CurseForge build.
