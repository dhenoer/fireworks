from ansi import cursor
from ansi.color import fg, fx
import numpy as np
import math
import random
import time
import threading
import playsound

# change this as you need
# --------------------

# constant TERMINAL size
TERMINAL_SIZE_COLS = 80 # 114 #80
TERMINAL_SIZE_ROWS = 24 # 48 #32

# default number of fireworks
DEFAULT_NFIRES = 15

# --------------------

# constant for Cartesian
X_AXIS_0 = TERMINAL_SIZE_ROWS//2 # screen row position 
Y_AXIS_0 = TERMINAL_SIZE_COLS//2 # screen col position
MAXROWORCOL = max(TERMINAL_SIZE_ROWS, TERMINAL_SIZE_COLS)
YRATIO = MAXROWORCOL / TERMINAL_SIZE_ROWS # Y Ratio
XRATIO = MAXROWORCOL / TERMINAL_SIZE_COLS # Y Ratio
MAXWIDTH = MAXROWORCOL / 4  # maximum scattered in screen

# constant for LargeDigits
# change X with chr(0x2588)
MAPDIGITS = '''
.XX....X..XXXX.XXXX.X..X.XXXX..XXX.XXXX.XXXX.XXXX..........
X..X..XX.....X....X.X..X.X....X.......X.X..X.X..X..XX......
X..X...X....X...XXX.XXXX.XXXX.XXXX....X..XX..XXXX..........
X..X...X..X.......X....X....X.X..X...X..X..X....X..XX......
.XX..XXXX.XXXX.XXXX....X.XXXX.XXXX..X...XXXX.XXX...........
'''
KEYDIGITS = '0123456789: '

class LargeDigits:

	aMapDigits = dict()
	posDigit = lambda self, i: i * 5

	def __init__(self):
		for d in MAPDIGITS.split('\n'):
			newd = d.replace(' ', '')
			newd = newd.replace('X', chr(0x2588))
			newd = newd.replace('.', ' ')
			if len(d)==0: continue
			for i,c in enumerate(KEYDIGITS):
				#print('i,c=',i,c)
				if self.aMapDigits.get(c,None) is None:
					self.aMapDigits[c] = []
				s = self.posDigit(i)
				self.aMapDigits[c].append(newd[s:s+5])
		#print(self.aMapDigits)

	def print(self, s, *, row=None, col=None):
		txt = []
		for c in s:
			txt.append(self.aMapDigits.get(c,''))

		#print('txt=',txt)
		for i in range(len(txt[0])):
			if all([row, col]):
				print(cursor.goto(row+i, col), end='')
			for c in txt:
				print(c[i], end=' ')
			print()
			

class Firework:

	delta_xy = (0,0)

	def fire(self):
		# start to fire
		self.shoot()
		self.explode()

	def shoot(self):
		# shoot fireworks

		playsound.playsound('woosh.mp3', False)
		# target
		dx = random.randint(-MAXWIDTH, MAXWIDTH) *XRATIO
		dy = random.randint(-MAXWIDTH//3, MAXWIDTH//2) *YRATIO
		self.delta_xy = (dx, dy)
		#print(self.delta_xy)

		# start position to shoot
		row = TERMINAL_SIZE_ROWS
		col = random.randint(1,TERMINAL_SIZE_COLS)

		x0, y0 = screenToCartesian((row,col))
		x1, y1 = (dx, dy)
		m = (y1 - y0)/(x1 - x0 + 1E-10)
		c = y0 - m * x0

		# model y = m*x + c

		for tick in [chr(0x387), ' ']:
			x = x0
			y = -np.inf
			while y < y1:
				y = m * x + c
				row, col = cartesianToScreen((x,y))
				
				print(cursor.goto(round(row), round(col)), end='')
				print(tick, end='', flush=True)
				if m >= 0: 
					x += 1.3
					#print(cursor.goto(round(row), round(col)), end='')
					#print('/', end='', flush=True)
				else: 
					x -= 1.3
					#print(cursor.goto(round(row), round(col)), end='')
					#print('\\', end='', flush=True)

				time.sleep(0.01)

	def explode(self):
		# explode fireworks

		sound = random.sample([
			'fireworks-1.mp3',
			'fireworks-2.mp3',
			'fireworks-3.mp3',
			'fireworks-4.mp3',
			'bomb.mp3',
		], 1)[0]
		playsound.playsound(f'{sound}', False)

		th = []
		idx = random.randint(0,2)
		for deg in range(0, 360, random.sample(range(20,50,5), 1)[0]):
			t = threading.Thread(target=self._particle, args=(deg,idx))
			t.start()
			th.append(t)

		for t in th:
			t.join()

	def _particle(self, angle=0, idxcolorset=0):
		# show particles

		maxwidth = MAXWIDTH * random.gauss(0.75,0.15)
		xpos = self._scatter(teta=angle, maxwidth=maxwidth)
		#print(xpos)
		colorSet = [
			[fg.red, fg.yellow, fg.white],
			[fg.yellow, fg.blue, fg.cyan],
			[fg.red, fg.blue, fg.white]
		]
		for tick in [chr(0x25AA), chr(0x25A0), chr(0x2593), chr(0x2591), ' ']:
			for i, (x,y) in enumerate(xpos):
				if tick==chr(0x2593):
					if random.randint(1,2)==1: continue
				x = round(x)
				y = round(y)
				if i < 3/5 * maxwidth:
					print(colorSet[idxcolorset][0], end='')
				elif i < 4/5 * maxwidth:
					print(colorSet[idxcolorset][1], end='')
				else:
					print(colorSet[idxcolorset][2], end='')
				rt, ct = cartesianToScreen((x,y), self.delta_xy)
				#print(f'## {yt} ##')
				print(cursor.goto(rt, ct), end='')
				print(tick, end='', flush=True)
				print(fx.reset, end='')
				time.sleep(random.randint(1,3)/100)
			time.sleep(random.randint(10,20)/100)

	def _scatter(self, *, tmax=20, maxwidth=20, teta=0):
		# calculate position of particle at time t

		# matrix of rotation based on teta angle
		teta = math.radians(teta)
		mrotate = np.matrix([[math.cos(teta), -math.sin(teta)],
					[math.sin(teta), math.cos(teta)]])

		# assume particle explode along x axis
		# x distance is proportional to maxwidth
		xpos = []
		for t in range(tmax, 0, -1):
			x = 5 * t**2
			if t == tmax: xmax = x
			xpos.append((int(x / xmax * maxwidth), 0))

		if random.randint(1,2)==1: xpos.reverse()

		# then rotate
		mxpos = np.matrix(xpos) * mrotate
		return mxpos.tolist()


def clearScreen():
	print(fx.reset, 
		cursor.erase(2),
		cursor.goto(1,1), end='', flush=True)

def cartesianToScreen( cart_coord, delta=(0,0)):
	x, y = cart_coord
	dx, dy = delta
	c = round(Y_AXIS_0 + (x + dx) / XRATIO )
	r = round(X_AXIS_0 - (y + dy) / YRATIO )
	return (r, c)

def screenToCartesian( screen_coord ):
	r, c = screen_coord
	x = round((c - Y_AXIS_0) * XRATIO )
	y = round((X_AXIS_0 - r) * YRATIO )
	return (x, y)

def title(nextYear):
	clearScreen()
	print(f'{fg.green}CountDown to NewYear {nextYear}{fx.reset}')
	print('-------------------------')

def hitEnter():
	print('\n-- Enter untuk lanjut')
	print(f'{fg.yellow}-- Hit Enter to continue{fx.reset}')
	input()


# main program -----------------------------------
nextYear = time.localtime().tm_year+1
title(nextYear)

print('\nProgram untuk menghitung mundur Tahun Baru')
print('diikuti peluncuran kembang api. File mp3')
print('untuk efek suara berasal dari http://soundbible.com')
print(f'{fg.yellow}This app used for countdown to the new year event')
print('followed by shooting of fireworks. All mp3 files')
print(f'for sound effect is credited to http://soundbible.com{fx.reset}')
print('\nFile *mp3 diletakkan pada folder yang sama')
print(f'{fg.yellow}Put *mp3 files to folder along application{fx.reset}')

hitEnter()

title(nextYear)
print('\nInput berapa detik lagi ke tahun baru, ')
print('atau [Enter] blank untuk hitung otomatis.')
print(f'{fg.yellow}Input how many seconds to the new year, ')
print(f'or just hit [Enter] for automatic calculation.{fx.reset}')
nsecs = input('(default localtime) > ')

print('\nBerapa kembang api yang akan diluncurkan?')
print(f'{fg.yellow}How many fireworks going to shoot?{fx.reset}')
nfires = input(f'(default {DEFAULT_NFIRES}) > ')
if nfires == '': nfires = DEFAULT_NFIRES
else: nfires = int(nfires)

if nsecs == '':
	tYEnd = time.mktime((nextYear,1,1,0,0,0,0,0,0))
	inputCountDown = round(tYEnd - time.time())
else:
	inputCountDown = int(nsecs)
	tYEnd = round(time.time() + inputCountDown)

if inputCountDown > 60*60*24: # more than 1 day
	print('\nTahun baru masih lama. Oleh karena itu yang')
	print('akan ditampilkan adalah jam / bukan countdown.')
	print(f'{fg.yellow}Too long for waiting. So application')
	print(f'will show clock, not countdown.{fx.reset}')
	hitEnter()


# display countdown waiting for new year..
title(nextYear)

labelCountDown = LargeDigits()
prev = ''
sound = False
while True :
	delta = int(round(tYEnd - time.time()))
	if delta < 0: break
	if delta <= 10 and not sound:
		sound = True
		playsound.playsound('countdown-10.mp3', False)
	
	if delta > 60*60*24 : #more than 1 day
		prev = 'clock'
		timestr = time.strftime('%H:%M:%S')
	else:
		timestr = str(delta)
		# if previouse mode is clock
		if prev == 'clock':
			clearScreen()
			prev = ''

	labelCountDown.print(f'{timestr} ', 
		row=X_AXIS_0-3, col= Y_AXIS_0-20)
	time.sleep(0.5)

# start firework -------
clearScreen()
listFw = []
while len(listFw) < nfires:
	f = Firework()
	fw = threading.Thread(target=f.fire)
	fw.start()
	listFw.append(fw)
	time.sleep(random.randint(5,15)/10)

for f in listFw:
	f.join()

clearScreen()
print(cursor.goto(X_AXIS_0, Y_AXIS_0-10), end='')
print(f'SELAMAT TAHUN BARU {nextYear}')
print(cursor.goto(X_AXIS_0+1, Y_AXIS_0-8), end='')
print(f'{fg.green}HAPPY NEW YEAR {nextYear}{fx.reset}')
input()

exit()
