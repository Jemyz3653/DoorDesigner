"""Draw original plank textures and four cutout patterns for every wood and dye."""
from pathlib import Path
from itertools import product
import json
import random
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'src/main/resources'
ASSETS=RES/'assets/doordesigner'
WOODS={'oak':(160,125,72),'spruce':(105,77,46),'birch':(202,185,132),'jungle':(156,111,78),
       'acacia':(175,89,53),'dark_oak':(68,45,26),'mangrove':(117,54,48),'cherry':(218,168,164),
       'bamboo':(191,169,77),'crimson':(116,54,82),'warped':(49,118,112),'pale_oak':(218,209,187),'poplar':(177,163,111)}
COLORS=[(249,255,254),(249,128,29),(199,78,189),(58,179,218),(254,216,61),(128,199,31),
        (243,139,170),(71,79,82),(157,157,151),(22,156,156),(137,50,184),(60,68,170),
        (131,84,50),(94,124,22),(176,46,38),(29,29,33)]

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')

def texture(wood,design,color,trap=False):
    rgb=WOODS[wood] if color==0 else tuple(int(a*.2+b*.8) for a,b in zip(WOODS[wood],COLORS[color-1]))
    im=Image.new('RGBA',(16,16 if trap else 32));rng=random.Random(wood+str(design))
    for y in range(im.height):
        for x in range(im.width):
            brightness=.67 if y%8==7 else rng.uniform(.88,1.09)
            im.putpixel((x,y),tuple(min(255,int(c*brightness)) for c in rgb)+(255,))
    draw=ImageDraw.Draw(im);clear=(0,0,0,0)
    if design==0:
        draw.rectangle((4,3,11,11 if trap else 18),fill=clear)
    elif design==1:
        for x in (3,9):
            for y in (3,9) if trap else (3,10,17):draw.rectangle((x,y,x+3,y+3),fill=clear)
    elif design==2:
        draw.ellipse((3,2,12,13 if trap else 15),fill=clear)
    else:
        for y in (3,7,11) if trap else (3,7,11,15,19):draw.rectangle((3,y,12,y+1),fill=clear)
    if not trap:draw.rectangle((12,19,13,21),fill=(112,108,94,255))
    return im

def model(name,parent,textures):
    write(ASSETS/'models/block'/f'{name}.json',{'parent':'minecraft:block/'+parent,'textures':textures})

def main():
    texture_dir=ASSETS/'textures/block';texture_dir.mkdir(parents=True,exist_ok=True)
    languages={locale:{'item.doordesigner.chisel':title} for locale,title in [('en_us','Door Chisel'),('ru_ru','Стамеска для дверей')]}
    for wood in WOODS:
        for trap in (False,True):
            base=wood+('_trapdoor' if trap else '_door');variants={};cases=[]
            for design,color in product(range(4),range(17)):
                name=f'{base}_{design}_{color}';im=texture(wood,design,color,trap)
                if trap:
                    im.save(texture_dir/(name+'.png'))
                    for part in ('bottom','top','open'):
                        model(name+'_'+part,'template_orientable_trapdoor_'+part,{'texture':'doordesigner:block/'+name})
                    for facing,half,opened in product(range(4),('bottom','top'),(False,True)):
                        part='open' if opened else half
                        entry={'model':f'doordesigner:block/{name}_{part}','y':facing*90}
                        if opened and half=='top':entry.update(x=180,y=(facing*90+180)%360)
                        key=f'design={design},color={color},facing={list(DIRECTIONS)[facing]},half={half},open={str(opened).lower()}'
                        variants[key]=entry
                    item_model=f'doordesigner:block/{name}_bottom'
                else:
                    for half in ('bottom','top'):
                        im.crop((0,16 if half=='bottom' else 0,16,32 if half=='bottom' else 16)).save(texture_dir/(name+'_'+half+'.png'))
                        for hinge,opened in product(('left','right'),(False,True)):
                            part=f'door_{half}_{hinge}'+('_open' if opened else '')
                            model(name+'_'+part,part,{key:f'doordesigner:block/{name}_{key}' for key in ('bottom','top')})
                    for facing,half,hinge,opened in product(range(4),('lower','upper'),('left','right'),(False,True)):
                        y=(facing*90-90+(90 if hinge=='left' else -90) * opened)%360
                        part=f'door_{"bottom" if half=="lower" else "top"}_{hinge}'+('_open' if opened else '')
                        key=f'design={design},color={color},facing={list(DIRECTIONS)[facing]},half={half},hinge={hinge},open={str(opened).lower()}'
                        variants[key]={'model':f'doordesigner:block/{name}_{part}','y':y}
                    icon=Image.new('RGBA',(16,16));icon.paste(im.resize((7,14),Image.Resampling.NEAREST),(4,1))
                    icon_path=ASSETS/'textures/item'/f'{name}.png';icon_path.parent.mkdir(parents=True,exist_ok=True);icon.save(icon_path)
                    write(ASSETS/'models/item'/f'{name}.json',{'parent':'minecraft:item/generated','textures':{'layer0':'doordesigner:item/'+name}})
                    item_model='doordesigner:item/'+name
                cases.append({'when':str(design),'model':{'type':'minecraft:model','model':item_model}})
            # The outer selector stores both dimensions without registering thousands of items.
            color_cases=[]
            for color in range(17):
                designs=[cases[design*17+color] for design in range(4)]
                color_cases.append({'when':str(color),'model':{'type':'minecraft:select','property':'minecraft:block_state',
                    'block_state_property':'design','cases':designs,'fallback':designs[0]['model']}})
            write(ASSETS/'items'/f'{base}.json',{'model':{'type':'minecraft:select','property':'minecraft:block_state',
                'block_state_property':'color','cases':color_cases,'fallback':color_cases[0]['model']}})
            write(ASSETS/'blockstates'/f'{base}.json',{'variants':variants})
            entry={'type':'minecraft:item','name':'doordesigner:'+base,'modifier':{
                'type':'minecraft:copy_state','block':'doordesigner:'+base,'properties':['design','color']}}
            if not trap:entry['condition']={'type':'minecraft:match_block','blocks':'doordesigner:'+base,'state':{'half':'lower'}}
            write(RES/'data/doordesigner/loot_table/blocks'/f'{base}.json',{'type':'minecraft:block','pools':[
                {'rolls':1,'condition':{'type':'minecraft:survives_explosion'},'entries':[entry]}]})
            for locale in languages:
                languages[locale]['block.doordesigner.'+base]=(wood.replace('_',' ').title()+' Designer '+('Trapdoor' if trap else 'Door')) if locale=='en_us' else ('Дизайнерский люк' if trap else 'Дизайнерская дверь')+' ('+wood+')'
    for locale,strings in languages.items():write(ASSETS/'lang'/f'{locale}.json',strings)
    all_blocks=['doordesigner:'+wood+suffix for wood in WOODS for suffix in ('_door','_trapdoor')]
    write(RES/'data/minecraft/tags/block/mineable/axe.json',{'values':all_blocks})
    for category in ('item','block'):
        for suffix,tag in [('_door','wooden_doors'),('_trapdoor','wooden_trapdoors')]:
            write(RES/f'data/minecraft/tags/{category}/{tag}.json',{'values':['doordesigner:'+wood+suffix for wood in WOODS]})
    write(RES/'data/doordesigner/recipe/chisel.json',{'type':'minecraft:crafting_shaped','category':'misc','pattern':[' I','C '],'key':{'I':'minecraft:iron_nugget','C':'minecraft:copper_ingot'},'result':{'id':'doordesigner:chisel'}})
    write(ASSETS/'items/chisel.json',{'model':{'type':'minecraft:model','model':'doordesigner:item/chisel'}})
    write(ASSETS/'models/item/chisel.json',{'parent':'minecraft:item/handheld','textures':{'layer0':'doordesigner:item/chisel'}})
    icon=Image.new('RGBA',(16,16));draw=ImageDraw.Draw(icon);draw.line((3,13,10,6),fill='#9a5d3d',width=3);draw.line((9,5,13,1),fill='#b8d0d1',width=3)
    icon.save(ASSETS/'textures/item/chisel.png')
    print('Generated 13 woods, four designs and 17 finishes for doors and trapdoors.')

DIRECTIONS={'north':0,'east':90,'south':180,'west':270}
if __name__=='__main__':main()
