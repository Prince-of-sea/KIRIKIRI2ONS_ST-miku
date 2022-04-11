import shutil
import chardet
import glob
import sys
import os
import re

same_hierarchy = (os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
scenario_dir = os.path.join(same_hierarchy,'scenario')
sound_dir = os.path.join(same_hierarchy,'sound')
image_dir = os.path.join(same_hierarchy,'image')
patch_dir = os.path.join(same_hierarchy,'patch')

layerCG_startnum=20
effect_startnum=10
effect_list=[]

#[w*]系統の命令一時変数預かり
trans_method = ''
trans_time = ''
quake_nsc = ''
move_nsc = ''

#--------------------def--------------------

# https://gist.github.com/PC-CNT/843e79e439a4dcba72f32602feafecf7
def conv1(moji :str) -> str:
	"""
	convert string to dictionary
	example:
	>>> conv1('a=test b="hoge hoge" c=true')
	{'a': 'test', 'b': 'hoge hoge', 'c': 'true'}
	"""
	outdic = {}
	for line in re.findall(r'(\S+?=(?:\".+\"|\S+))', moji):
		key, value = re.split(r'=', line, 1)
		outdic[key] = value.strip('"')
	return outdic

def effect_edit(t,f):
	global effect_list

	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list)+effect_startnum

	return str(list_num)

def def_kakkoline(line):
	global trans_method
	global trans_time
	global quake_nsc
	global move_nsc

	linedef = line
	kr_cmd = kakko_dict['kr_cmd']

	if kr_cmd == 'jump':
		line = 'goto *' + str(kakko_dict.get('storage')).replace('.', '_')#goto先のラベル名
	
	elif kr_cmd == 'c':
		line = 'print 0'

	elif kr_cmd == 'wait':
		time = kakko_dict.get('time')
		cond = kakko_dict.get('cond')

		if re.fullmatch(r'[0-9]+',time):#timeが数字のみ＝本処理
			line = 'wait ' + time

			if cond =='kag.skipMode >= 3':
				line = 'isskip %8:if %8==1 ' + line
			elif cond =='kag.skipMode < 3':
				line = 'isskip %8:if %8!=1 ' + line

	elif kr_cmd == 'hsDispEvent':
		#visible = kakko_dict.get('visible')
		storage = kakko_dict.get('storage')
		mode = kakko_dict.get('mode') if kakko_dict.get('mode') else '0'
		time = kakko_dict.get('time') if kakko_dict.get('time') else '1500'
		time2 = str(int(int(time)/2))

		if mode == '0':#CG - 通常フェード
			line = 'cltati:bgdef "image\\' + storage + '.png",' + effect_edit(time, 'fade')
		elif mode == '1':#CG - 白
				line = 'cltati:bgdef ":c;bgimage\\bg_white.bmp",' + effect_edit(time2, 'fade') + 'lsp 5,":a;image\\' + storage + '.png",0,0:print ' + effect_edit(time2, 'fade')
		elif mode == '2':#CG - 黒
			line = 'cltati:bgdef ":c;bgimage\\bg_black.bmp",' + effect_edit(time2, 'fade') + 'lsp 5,":a;image\\' + storage + '.png",0,0:print ' + effect_edit(time2, 'fade')
		elif mode == '4':#背景 - 黒
			line = 'cltati:bgdef ":c;bgimage\\bg_black.bmp",' + effect_edit(time2, 'fade') + 'bgdef "bgimage\\' + storage + '.png",' + effect_edit(time2, 'fade')

	elif kr_cmd == 'image':
		#visible = kakko_dict.get('visible')
		grayscale = kakko_dict.get('grayscale')
		storage = kakko_dict.get('storage')
		layer = kakko_dict.get('layer')

		if layer == 'base':
			line = 'cltati:bgdef "bgimage\\' + storage + '.png",2'

		else:
			#opacity = kakko_dict.get('opacity')
			#page = kakko_dict.get('page')
			left = kakko_dict.get('left') if kakko_dict.get('left') else '0'
			top = kakko_dict.get('top') if kakko_dict.get('top') else '0'
			pos = kakko_dict.get('pos')

			#kr→nscレイヤー   0=cg[s5] / 1=cg上[s4] / 2=カットイン[s3]  他は適当
			layer2 = str(int(5-int(layer)))
			if not pos:
				line = 'lsph ' + layer2 + ',":a;image\\' + storage + '.png",' + left + ',' + top + ':print 2'
			else:
				if pos == 'c':
					#今作見た感じposはfgimageのcしかなさそう
					line = 'tati ":a;fgimage\\' + storage + '.png","",' + layer2
		
		if grayscale:#今作のモノクロ全部セピアっぽい
			line = 'monocro #eeccaa:print 0:' + line

	elif kr_cmd == 'trans':
		trans_method = kakko_dict.get('method')
		trans_time = kakko_dict.get('time')
		line = ';処理済\t' + line

	elif kr_cmd == 'wt':
		#if trans_method == 'crossfade':#どうせ全部crossfade
		if True:
			trans_method2 = 'fade'
		
		line = 'vsp 3,1:vsp 4,1:vsp 5,1:print ' + effect_edit(trans_time, trans_method2)

		#保険
		trans_method = ''
		trans_time = ''

	elif kr_cmd == 'quake':
		time = kakko_dict.get('time')
		hmax = kakko_dict.get('hmax')#x?
		vmax = kakko_dict.get('vmax')#y?

		if (not hmax) and (not vmax):
			quake_nsc = 'quake 10,' + time
		elif hmax == vmax:
			quake_nsc = 'quake ' + hmax + ',' + time
		elif vmax == '0':
			quake_nsc = 'isskip %8:if %8==1 quakex ' + hmax + ',' + time
		elif hmax == '0':
			quake_nsc = 'isskip %8:if %8==1 quakey ' + vmax + ',' + time
		else:
			quake_nsc = 'isskip %8:if %8==1 quakex ' + hmax + ',' + time + ':quakey ' + vmax + ',' + time

		line = ';処理済\t' + line

	elif kr_cmd == 'wq':
		line = quake_nsc

		#保険
		quake_nsc = ''

	elif kr_cmd == 'hsChgCutin':
		storage = kakko_dict.get('storage')
		if storage:
			line = 'tati ":a;image\\' + storage + '.png","",3'
		else:
			line = 'csp 3:print 2'

	elif kr_cmd == 'hsBlackout':
		#visible = kakko_dict.get('visible')
		time = kakko_dict.get('time') if kakko_dict.get('time') else '750'

		line ='cltati:bgdef ":c;bgimage\\bg_black.bmp",' + effect_edit(time, 'fade')

	elif kr_cmd == 'hsWhiteout':
		#visible = kakko_dict.get('visible')
		time = kakko_dict.get('time') if kakko_dict.get('time') else '750'

		line ='cltati:bgdef ":c;bgimage\\bg_white.bmp",' + effect_edit(time, 'fade')

	elif kr_cmd == 'hsDispMsg':
		line = 'vsp 2,1:vsp 6,1'

	elif kr_cmd == 'hsChgBgi':
		storage = kakko_dict.get('storage')
		time = kakko_dict.get('time') if kakko_dict.get('time') else '1000'
		rule = kakko_dict.get('rule') if kakko_dict.get('rule') else 'fade'

		line = 'cltati:bgdef "bgimage\\' + storage + '.png",' + effect_edit(time, rule)

	elif kr_cmd == 'hsChgFgi':
		storage1 = kakko_dict.get('storage1')
		pos1 = kakko_dict.get('pos1') if kakko_dict.get('pos1') else ''

		if storage1:
			line = 'tati ":a;fgimage\\' + storage1 + '.png","' + pos1 + '",6:print 2'
		else:
			line = 'vsp 6,0'

	elif kr_cmd == 'move':
		#accel = kakko_dict.get('accel')
		layer = kakko_dict.get('layer')
		time = kakko_dict.get('time')
		path = kakko_dict.get('path')

		#kr→nscレイヤー   0=cg[s5] / 1=cg上[s4] / 2=カットイン[s3]  他は適当
		layer2 = str(int(5-int(layer)))

		path_list = re.findall(r'\(([0-9-]+),([0-9-]+),([0-9-]+)\)', path)
		time2 = str(int(int(time)/len(path_list)))

		for a in path_list:
			move_nsc += ':' if (not move_nsc == '') else ''			
			move_nsc += 'layermove '+layer2+','+effect_edit(time2, 'fade')+','+a[0]+','+a[1]+','+a[2]

		line = ';処理済\t' + line

	elif kr_cmd == 'wm':
		line = move_nsc
		move_nsc = ''
	
	elif kr_cmd == 'hsFlush':
		storage = kakko_dict.get('storage')#どうせ白塗り
		line = 'lsp 3,"bgimage\\' + storage + '.png":print 2:csp 3:print 2'

	elif kr_cmd == 'hsPlaySE':
		storage = kakko_dict.get('storage')
		sound_name = sound_dict.get(str(storage).lower())
		if storage and sound_name:
			line = 'dwave 0,"sound\\' + sound_name + '.ogg"'
		else:
			line = 'dwavestop 0'

	elif kr_cmd == 'hsChgBgm':
		#volume = kakko_dict.get('volume')
		#loop = kakko_dict.get('loop')
		storage = kakko_dict.get('storage')

		if storage:
			line = 'bgm "bgm\\' + storage + '.ogg"'

	elif kr_cmd == 'xchgbgm':
		#overlap = kakko_dict.get('overlap')
		#time = kakko_dict.get('time')
		storage = kakko_dict.get('storage')

		if storage:
			line = 'bgm "bgm\\' + storage + '.ogg"'

	elif kr_cmd == 'fadeinbgm':
		#loop = kakko_dict.get('loop')
		time = kakko_dict.get('time')
		storage = kakko_dict.get('storage')

		if storage:
			line = 'playfadein "bgm\\' + storage + '.ogg",' + time

	elif kr_cmd == 'fadeoutbgm':
		time = kakko_dict.get('time')

		line = 'stopfadeout '+ time

	elif kr_cmd == 'stopbgm':
		line = 'bgmstop'

	elif kr_cmd == 'playvideo':
		storage = kakko_dict.get('storage')

		line = 'mpegplay "video\\' + storage + '",%200'

	elif kr_cmd == 'hsEnd':
		line = 'mov %200,1:reset'

	#無変更時コメントアウト/変更時末尾に改行挿入
	line = r';' + line if linedef == line else line + '\n'

	return line


#--------------------ファイル整理--------------------

#パッチ適用
for patch_path in glob.glob(os.path.join(patch_dir, '*')):
	ext = (os.path.splitext(patch_path)[1]).lower()
	if ext == '.ks':
		extdir = scenario_dir
	elif ext == '.png':
		extdir = image_dir
	else:
		extdir = ''

	if extdir:
		patch_path2 = os.path.join(extdir,os.path.basename(patch_path))
		shutil.move(patch_path, patch_path2)

#音源リネーム
sound_dict = {}
for i,sound_path in enumerate( glob.glob(os.path.join(sound_dir, '*')) ):
	sound_path2 = os.path.join(os.path.dirname(sound_path), 'sound'+str(i)+os.path.splitext(sound_path)[1])
	os.rename(sound_path, sound_path2)
	
	sound_dict[(os.path.splitext(os.path.basename(sound_path))[0]).lower()] = 'sound'+str(i)


#--------------------0.txt作成--------------------

with open(os.path.join(same_hierarchy, 'default.txt')) as f:
	txt = f.read()

for ks_path in glob.glob(os.path.join(scenario_dir, '*')):
	
	with open(ks_path, 'rb') as f:
		char_code =chardet.detect(f.read())['encoding']

	with open(ks_path, encoding=char_code, errors='ignore') as f:
		#ks名をそのままonsのgoto先のラベルとして使い回す
		txt += 'end\n\n*' + os.path.splitext(os.path.basename(ks_path))[0] + '_ks\n'

		for line in f:
			#最初にやっとくこと
			line = re.sub(r'\[ruby text="(.+?)"\](.)',r'(\2/\1)',line)#ルビ置換
	
			name_line = re.fullmatch(r'\[stName\](.+?)\[endName\]\n',line)#括弧行定義
			kakko_line = re.fullmatch(r'\[(.+?)\]\n',line)#括弧行定義
			str_line = re.fullmatch(r'(.+?)(\[w( mode=l)?\])?\n',line)#文章行定義

			if re.search('^\n', line):#空行
				pass#そのまま放置

			elif re.match(r'\*', line):#nsc側でラベルと勘違いするの対策
				line = r';' + line#エラー防止の為コメントアウト

			elif re.search(';', line):#元々のメモ
				line = line.replace(';', ';;;')#分かりやすく

			elif name_line:
				line = 'mov $1,"'+name_line[1]+'"\n'

			elif kakko_line:
				kakko_dict = conv1('kr_cmd=' + kakko_line[1])
				line = def_kakkoline(line)

			elif str_line:
				if str_line[2]:
					s='3' if str_line[3] else '2'
				else:
					s='1'

				line = 'msg "'+str_line[1]+'",'+s+'\n'

			else:#どれにも当てはまらない、よく分からない場合
				#print('err!:   '+line)
				line = r';' + line#エラー防止の為コメントアウト

			txt += line

add0txt_graphic = ''
for im_path in glob.glob(os.path.join(image_dir, '*')):
	imname = (os.path.splitext(os.path.basename(im_path))[0])
	imfin = re.findall(r'ev_(..)_.{1,3}',imname)
	if imfin:
		add0txt_graphic += ('if $6=="'+imfin[0]+'" bg black,3:bg "image\\'+imname+'.png",3:click\n')

add0txt_effect = ''
for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換

	if e[1] == 'fade':
		add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'

	else:
		add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"rule\\'+e[1]+'.png"\n'

txt = txt.replace(r';<<-SE-DWAVE->>', 'dwave 0,"sound\\' + sound_dict['se_click'] + '.ogg"')
txt = txt.replace(r';<<-GRAPHIC_VIEW->>', add0txt_graphic)
txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

open(os.path.join(same_hierarchy,'0.txt'), 'w', errors='ignore').write(txt)