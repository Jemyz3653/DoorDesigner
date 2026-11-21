package studio.detemkur.doordesigner;

import java.util.*;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.core.*;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.*;
import net.minecraft.resources.*;
import net.minecraft.world.*;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.*;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.state.*;
import net.minecraft.world.level.block.state.properties.*;

public final class DoorDesigner implements ModInitializer {
    public static final IntegerProperty DESIGN=IntegerProperty.create("design",0,3);
    public static final IntegerProperty COLOR=IntegerProperty.create("color",0,16);
    public static final List<String> WOODS=List.of("oak","spruce","birch","jungle","acacia","dark_oak",
        "mangrove","cherry","bamboo","crimson","warped","pale_oak","poplar");
    public static final Map<String,Block> DOORS=new LinkedHashMap<>(),TRAPDOORS=new LinkedHashMap<>();
    public static Item CHISEL;
    public static Identifier id(String path) { return Identifier.fromNamespaceAndPath("doordesigner",path); }
    @Override public void onInitialize() {
        for (String wood:WOODS) {
            DOORS.put(wood,register(wood,true));
            TRAPDOORS.put(wood,register(wood,false));
        }
        var key=ResourceKey.create(Registries.ITEM,id("chisel"));
        CHISEL=Registry.register(BuiltInRegistries.ITEM,key,new Chisel(new Item.Properties().setId(key).stacksTo(1)));
        CreativeModeTabEvents.modifyOutputEvent(ResourceKey.create(Registries.CREATIVE_MODE_TAB,
            Identifier.fromNamespaceAndPath("minecraft","functional_blocks"))).register(entries -> {
                entries.accept(CHISEL); DOORS.values().forEach(entries::accept); TRAPDOORS.values().forEach(entries::accept);
            });
        UseBlockCallback.EVENT.register((player,level,hand,hit) -> {
            var state=level.getBlockState(hit.getBlockPos());
            var dye=player.getItemInHand(hand).get(DataComponents.DYE);
            if (dye==null || !state.hasProperty(COLOR) || !state.hasProperty(DESIGN)
                || !BuiltInRegistries.BLOCK.getKey(state.getBlock()).getNamespace().equals("doordesigner")
                || state.getValue(COLOR)==dye.ordinal()+1) return InteractionResult.PASS;
            if (!level.isClientSide() && change(level,hit.getBlockPos(),state.setValue(COLOR,dye.ordinal()+1),player))
                player.getItemInHand(hand).consume(1,player);
            return InteractionResult.SUCCESS;
        });
    }
    private static Block register(String wood,boolean door) {
        String path=wood+(door ? "_door" : "_trapdoor");
        var base=BuiltInRegistries.BLOCK.getValue(Identifier.fromNamespaceAndPath("minecraft",path));
        var type=((DoorBlock)BuiltInRegistries.BLOCK.getValue(Identifier.fromNamespaceAndPath("minecraft",wood+"_door"))).type();
        var key=ResourceKey.create(Registries.BLOCK,id(path));
        var properties=BlockBehaviour.Properties.ofFullCopy(base).setId(key).noOcclusion();
        Block block=Registry.register(BuiltInRegistries.BLOCK,key,door ? new DesignedDoor(type,properties) : new DesignedTrapdoor(type,properties));
        var itemKey=ResourceKey.create(Registries.ITEM,id(path));
        var itemProperties=new Item.Properties().setId(itemKey).useBlockDescriptionPrefix();
        Registry.register(BuiltInRegistries.ITEM,itemKey,door ? new DoubleHighBlockItem(block,itemProperties) : new BlockItem(block,itemProperties));
        return block;
    }
    public static boolean change(Level level,BlockPos pos,BlockState next,Player player) {
        var old=level.getBlockState(pos);
        if (!(level instanceof net.minecraft.server.level.ServerLevel server)
            || !player.getAbilities().mayBuild || !player.mayInteract(server,pos)) return false;
        BlockPos other=null;
        if (old.getBlock() instanceof DoorBlock) {
            other=old.getValue(DoorBlock.HALF)==DoubleBlockHalf.LOWER ? pos.above() : pos.below();
            if (!level.getBlockState(other).is(old.getBlock()) || !player.mayInteract(server,other)) return false;
        }
        int flags=Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;
        level.setBlock(pos,next,flags);
        if (other!=null) {
            var opposite=next.getValue(DoorBlock.HALF)==DoubleBlockHalf.LOWER ? DoubleBlockHalf.UPPER : DoubleBlockHalf.LOWER;
            level.setBlock(other,next.setValue(DoorBlock.HALF,opposite),flags);
            level.updateNeighborsAt(other,next.getBlock());
        }
        level.updateNeighborsAt(pos,next.getBlock());
        return true;
    }
    private static BlockState copy(BlockState source,Block target) {
        var result=target.defaultBlockState();
        for (var property:source.getProperties()) if (result.hasProperty(property)) result=copyProperty(source,result,property);
        return result;
    }
    private static <T extends Comparable<T>> BlockState copyProperty(BlockState source,BlockState result,Property<T> property) {
        return result.setValue(property,source.getValue(property));
    }
    static final class Chisel extends Item {
        Chisel(Properties properties) { super(properties); }
        @Override public InteractionResult useOn(UseOnContext context) {
            var player=context.getPlayer();
            if (player==null) return InteractionResult.PASS;
            var level=context.getLevel();var pos=context.getClickedPos();var state=level.getBlockState(pos);
            boolean door=state.getBlock() instanceof DoorBlock;
            if (!door && !(state.getBlock() instanceof TrapDoorBlock)) return InteractionResult.PASS;
            var id=BuiltInRegistries.BLOCK.getKey(state.getBlock());
            BlockState result;
            if (id.getNamespace().equals("doordesigner")) {
                result=state.setValue(DESIGN,Math.floorMod(state.getValue(DESIGN)+(player.isShiftKeyDown() ? -1 : 1),4));
            } else {
                if (!id.getNamespace().equals("minecraft") && !id.getNamespace().equals("coloredm")) return InteractionResult.PASS;
                String material=id.getPath();int color=0;
                if (id.getNamespace().equals("coloredm")) {
                    for (var dye:DyeColor.values()) {
                        if (material.startsWith(dye.getName()+"_")) {
                            material=material.substring(dye.getName().length()+1);color=dye.ordinal()+1;break;
                        }
                    }
                }
                String wood=material.equals("door") || material.equals("trapdoor") ? "oak"
                    : material.substring(0,material.length()-(door ? 5 : 9));
                var target=(door ? DOORS : TRAPDOORS).get(wood);
                if (target==null) return InteractionResult.PASS;
                result=copy(state,target).setValue(COLOR,color);
            }
            if (!level.isClientSide()) change(level,pos,result,player);
            return InteractionResult.SUCCESS;
        }
    }
    static final class DesignedDoor extends DoorBlock {
        DesignedDoor(BlockSetType type,Properties properties) {
            super(type,properties); registerDefaultState(defaultBlockState().setValue(DESIGN,0).setValue(COLOR,0));
        }
        @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> builder) {
            super.createBlockStateDefinition(builder);builder.add(DESIGN,COLOR);
        }
    }
    static final class DesignedTrapdoor extends TrapDoorBlock {
        DesignedTrapdoor(BlockSetType type,Properties properties) {
            super(type,properties);registerDefaultState(defaultBlockState().setValue(DESIGN,0).setValue(COLOR,0));
        }
        @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> builder) {
            super.createBlockStateDefinition(builder);builder.add(DESIGN,COLOR);
        }
    }
}
