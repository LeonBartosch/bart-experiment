
# A simple version of the Balloon Analog Risk Task (BART) written with PsychoPy.
# This experiment is a computerized, laboratory-based measure that involves actual
# risky behavior for which, similar to real-world situations, riskiness is rewarded
# up until a point at which further riskiness results in poorer outcomes.
# Participants complete 90 trials where they pump a balloon and obtain money.
# With every pump a balloon wil explode with increasing probability (Lejuez et al. 2002).
# Subject and data will be seperately stored in txt files and can be matched by subject id.

# It is entirely based on:
# Lejuez, C. W., Read, J. P., Kahler, C. W., Richards, J. B., Ramsey, S. E., Stuart, G. L., ... & Brown, R. A. (2002).
# Evaluation of a behavioral measure of risk taking: the Balloon Analogue Risk Task (BART).
# Journal of Experimental Psychology: Applied, 8(2), 75-84. http://dx.doi.org/10.1037/1076-898X.8.2.75
# source: http://www.impulsivity.org/measurement/BART


import random
import socket
import threading
import json
import time
from psychopy import core, data, event, gui, sound, visual


# window and stimulus sizes
WIN_WIDTH = 1280
WIN_HEIGHT = 720
POP_TEXTURE_SIZE = (200, 155)
BALL_TEXTURE_SIZE = (596, 720)
INITIAL_BALL_SIZE = (
    int(BALL_TEXTURE_SIZE[0] * 0.2), int(BALL_TEXTURE_SIZE[1] * 0.2))
# ball size increases starting at 20% of screen hight until 100% for condition with maximal 128 pumps

# task configuration
COLOR_LIST = ['yellow', 'orange', 'blue']
MAX_PUMPS = [16, 48, 128]  # three risk types
REPETITIONS = 5  # repetitions of risk
REPETITIONS_PRACTICE = 2 # repetitions of practice
REWARD = 0.05
WEIGHT = 0.01

# keys
KEY_PUMP = 'space'
KEY_NEXT = 'return'
KEY_QUIT = 'escape'

# messages
ABSENT_MESSAGE = 'You\'ve waited to long! The balloon has shrunk. Your temporary earnings are lost.'
FINAL_MESSAGE = 'Well done! You banked a total of {:.2f} €.'

# sounds
slot_machine = sound.Sound('slot_machine.ogg')
pop_sound = sound.Sound('pop.ogg')

SERVER_IP = '192.168.0.137'
PORT = 5555

# network
class NetworkClient:
    def __init__(self, player_id, server_ip, port=PORT):
        self.player_id = player_id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_ip, port))
        self.leaderboard = []
        self.running = True
        threading.Thread(target=self.listen_for_updates, daemon=True).start()

    def listen_for_updates(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
                if data:
                    self.leaderboard = json.loads(data.decode())
                    print("[LEADERBOARD]", self.leaderboard)
            except Exception as e:
                print("[ERROR] Listening failed:", e)
                self.running = False

    def send_update(self, pumps):
        msg = {"id": self.player_id, "pumps": pumps}
        try:
            self.sock.sendall(json.dumps(msg).encode())
        except Exception as e:
            print("[ERROR] Sending failed:", e)

    def get_leaderboard(self):
        return self.leaderboard

    def close(self):
        self.running = False
        self.sock.close()


# global objects

# create window
win = visual.Window(
    size=(WIN_WIDTH, WIN_HEIGHT),
    units='pix',
    color='Black',
    fullscr=False
)
# stimulus
stim = visual.ImageStim(
    win,
    pos=(0, 0),
    size=INITIAL_BALL_SIZE,
    units='pix',
    interpolate=True
)
# text
text = visual.TextStim(
    win,
    color='White',
    height=0.08,
    pos=(0.4, -0.9),
    alignText='right',
    units='norm',
    anchorHoriz='center',
    anchorVert='bottom'
)
remind_return = visual.TextStim(
    win,
    color='White',
    height=0.08,
    pos=(-0.2, -0.9),
    alignText='right',
    units='norm',
    anchorHoriz='right',
    anchorVert='bottom'
)
remind_enter = visual.TextStim(
    win,
    color='White',
    height=0.08,
    pos=(0.2, -0.9),
    alignText='left',
    units='norm',
    anchorHoriz='left',
    anchorVert='bottom'
)
leaderboard_stim = visual.TextStim(
    win,
    text="",
    pos=(0.6, 0),
    font="Courier",
)    


def showInfoBox():
    """Set up dialog box for subject information."""
    info = {
        'id': '0',
        'age': '0',
        'version': 0.1,
        'gender': ['female', 'male', 'other'],
        'date': data.getDateStr(format="%Y-%m-%d_%H:%M"),
        'server_ip': SERVER_IP
    }
    return gui.DlgFromDict(
        title='BART',
        dictionary=info,
        fixed=['version'],
        order=['id', 'age', 'gender', 'date', 'server_ip', 'version']
    )


def createTrialHandler(colorList, maxPumps, REPETITIONS, REWARD):
    """Creates a TrialHandler based on colors of balloon and pop stimuli, repetitions of trials and reward value for
    each successful pump. CAVE: color_list and maxPumps must be lists of equal length."""
    # to import balloon and pop images of different colors
    balloonImg = []
    popImg = []
    for color in colorList:
        balloonImg.append(color + 'Balloon.png')
        popImg.append(color + 'Pop.png')
    # create trial list of dictionaries
    trialList = []
    for index in range(len(colorList)):
        trialDef = {
            'balloon_img': balloonImg[index],
            'pop_img': popImg[index],
            'maxPumps': maxPumps[index],
            'reward': REWARD
        }
        trialList.append(trialDef)
    # same order for all subjects
    random.seed(52472)
    trials = data.TrialHandler(
        trialList,
        nReps=REPETITIONS,
        method='fullRandom'
    )
    return trials


def showInstruction(img, wait=300):
    """Show an instruction and wait for a response"""
    instruction = visual.ImageStim(
        win,
        image=img,
        pos=(0, 0),
        size=(2, 2),
        units='norm'
    )
    instruction.draw()
    win.flip()
    respond = event.waitKeys(
        keyList=[KEY_PUMP, KEY_QUIT],
        maxWait=wait
    )
    key = KEY_QUIT if not respond else respond[0]
    return key


def drawText(TextStim, pos, txt, alignment='center'):
    """Takes a PsychoPy TextStim and updates position and text before drawing the stimulus."""
    TextStim.pos = (pos)
    TextStim.setText(txt)
    if hasattr(TextStim, 'alignHoriz'):  # Sicherer, auch für alte/neue PsychoPy-Versionen
        TextStim.alignHoriz = alignment
    TextStim.draw()


def showImg(img, size, wait=1):
    """Shows an image of spezified size."""
    stim.setImage(img)
    stim.size = size
    stim.draw()
    win.flip()
    core.wait(wait)


def saveData(dataList, file="data.txt"):
    """"Saves all relevant data in txt file."""
    output = '\t'.join(map(str, dataList)) + '\n'
    with open(file, 'a') as outputFile:
        outputFile.write(output.format(dataList))


def drawTrial(ballSize, ballImage, lastMoney, totalMoney):
    """Shows trial setup, i.e. reminders, stimulus, and account balance."""
    stim.size = ballSize
    stim.setImage(ballImage)
    stim.draw()
    drawText(remind_return, (-0.23, -0.9),
             'Press ENTER\nto cash earnings', 'right')
    drawText(remind_enter, (0.23, -0.9),
             'Press SPACE\nto pump', 'left')
    drawText(text, (0.4, -0.6),
             'Last Balloon: \n{:.2f} €'.format(lastMoney))
    drawText(text, (0.4, -0.9),
             'Total Earned: \n{:.2f} €'.format(round(totalMoney, 2)))
    win.flip()
    
def get_estimate(min_value, max_value, ballImage, win):
    error_message = ""
    input_text = ""
    cursor_visible = True
    
    max_digits = len(str(max_value))
    
    last_blink = time.time()
    blink_interval = 0.5  # Sekunden
    
    prompt = visual.TextStim(
        win, text="This will be your next balloon. It can take " + str(max_value) + " Pumps at most. \nHow many pumps do you think you can achieve before popping the balloon?",
        pos=(0, -0.5), height=0.08, units='norm'
    )
    error_disp = visual.TextStim(
        win, text="", pos=(0, 0.5), color='red', height=0.08, units='norm'
    )
    input_disp = visual.TextStim(
        win, text="", pos=(0, -0.8), color='yellow', height=0.08, units='norm'
    )
    
    while True:
        if time.time() - last_blink > blink_interval:
            cursor_visible = not cursor_visible
            last_blink = time.time()
        display_text = input_text + ('|' if cursor_visible else '')
        
        stim.size = INITIAL_BALL_SIZE
        stim.setImage(ballImage)
        stim.draw()
        
        prompt.draw()
        
        input_disp.text = display_text
        input_disp.draw()
        
        if error_message:
            error_disp.text = error_message
            error_disp.draw()
            
        win.flip()
        
        keys = event.getKeys()        
        
        if keys:
            for key in keys:
                if key in ['return', 'num_enter']:
                    if input_text.isdigit():
                        user_input = int(input_text)
                        if min_value <= user_input <= max_value:
                            return user_input
                        else:
                            error_message = f"⚠ The number must be between {min_value} and {max_value}!"
                    else:
                        error_message = "⚠ Invalid Entry! Please enter a whole number."
                elif key in ['backspace']:
                    input_text = input_text[:-1]
                elif key in ['escape']:
                    core.quit()
                elif key.isdigit():
                    if len(input_text) < max_digits:
                        input_text += key
                    if int(input_text) > max_value:
                        input_text = str(max_value)

def drawLeaderboard(leaderboard, leaderboard_stim, my_id, win, wait=2):
    if leaderboard:
        my_id = str(my_id)  # als String vergleichen
        leaderboard_text = "Leaderboard\n\n"
        leaderboard_text += f"{'Rank':<5}{'Player':<16}{'Pumps':>7}\n"
        leaderboard_text += "-" * 32 + "\n"
        for i, entry in enumerate(leaderboard, start=1):
            pid = str(entry['id'])
            if pid.isdigit():
                player_num = f"Player {int(pid) + 1}"
            else:
                player_num = pid
            if pid == my_id:
                player_label = f"{player_num} (You)"
            else:
                player_label = player_num
            if str(entry['id']) == my_id:
                player_label = f"{player_num} (You)"
            else:
                player_label = player_num
            leaderboard_text += f"{i:<5}{player_label:<16}{entry['pumps']:>7}\n"
        drawText(leaderboard_stim, (0.6, 0), leaderboard_text, alignment='left')
        win.flip()
        core.wait(wait)

def bart(info, net_client):
    """Execute experiment"""
    trials = createTrialHandler(COLOR_LIST, MAX_PUMPS, REPETITIONS, REWARD)

    if showInstruction('instructions.png') == KEY_QUIT:
        return
        
    permBank = 0
    lastTempBank = 0
    # iterate thorugh balloons
    for trialNumber, trial in enumerate(trials):

        # trial default settings
        tempBank = 0  # temporary bank
        pop = False
        nPumps = 0
        continuePumping = True
        increase = 0
        ballSize = INITIAL_BALL_SIZE
        stim.size = ballSize
        
        current_leaderboard = net_client.get_leaderboard()
        drawLeaderboard(current_leaderboard, leaderboard_stim, info['id'], win)
        
        estimate = get_estimate(
            min_value=1,
            max_value=trial['maxPumps'],
            ballImage=trial['balloon_img'],
            win=win
        )
        
        # pump balloon
        while continuePumping and not pop:

            # increases ball size with each pump
            ballSize = (
                INITIAL_BALL_SIZE[0] + BALL_TEXTURE_SIZE[0] * increase,
                INITIAL_BALL_SIZE[1] + BALL_TEXTURE_SIZE[1] * increase
            )

            drawTrial(ballSize, trial['balloon_img'], lastTempBank, permBank)

            # process response
            respond = event.waitKeys(
                keyList=[KEY_PUMP, KEY_NEXT, KEY_QUIT],
                maxWait=15
            )

            # no response - continue to next balloon
            if not respond:
                drawText(
                    text, (0, 0), ABSENT_MESSAGE, 'center')
                win.flip()
                core.wait(5)
                continuePumping = False

            # escape key pressed
            elif respond[0] == KEY_QUIT:
                return

            # cash out key pressed
            elif respond[0] == KEY_NEXT:
                lastTempBank = tempBank
                slot_machine.stop()
                slot_machine.play()

                # Im bart() nach dem Pumpen (oder nach jedem trial)
                net_client.send_update(nPumps)

                # aninmation: count up to new balance
                newBalance = permBank + tempBank
                while round(permBank, 2) < round(newBalance, 2):
                    permBank += 0.01
                    drawText(text, (0.4, -0.6),
                             'Last Balloon: \n{:.2f} €'.format(tempBank))
                    drawText(text, (0.4, -0.9),
                             'Total Earned:\n{:.2f} €'.format(permBank))
                    win.flip()
                permBank = newBalance
                continuePumping = False

            # pump key pressed
            elif respond[0] == KEY_PUMP:
                nPumps += 1

                # determine whether balloon pops or not
                if random.random() < 1.0 / (trial['maxPumps'] - nPumps):
                    pop_sound.stop()
                    pop_sound.play()
                    showImg(trial['pop_img'], POP_TEXTURE_SIZE)
                    lastTempBank = 0
                    pop = True
                else:
                    if nPumps > estimate:
                        tempBank = estimate*REWARD
                    else:
                        tempBank = max(0, nPumps*REWARD - WEIGHT*(estimate-nPumps))
                    
                    # increase balloon size to fill up other 80%
                    increase += 0.8 / max(MAX_PUMPS)

            # save list of data in txt file
            dataList = [info['id'], trialNumber,
                        trial['maxPumps'], estimate, nPumps, pop, '{:.2f}'.format(permBank)]
            saveData(dataList, 'data.txt')
    subjectList = [info['id'], info['age'], info['gender'], info['date']]
    saveData(subjectList, 'subjects.txt')

    # final information about reward
    drawText(text, (0, 0),
             FINAL_MESSAGE.format(permBank), 'center')
    win.flip()
    core.wait(5)
    return

def bart_practice(info, net_client):
    """Execute experiment"""
    trials = createTrialHandler(COLOR_LIST, MAX_PUMPS, REPETITIONS_PRACTICE, REWARD)

    if showInstruction('instructions_practice.png') == KEY_QUIT:
        return
        
    permBank = 0
    lastTempBank = 0
    # iterate thorugh balloons
    for trialNumber, trial in enumerate(trials):

        # trial default settings
        tempBank = 0  # temporary bank
        pop = False
        nPumps = 0
        continuePumping = True
        increase = 0
        ballSize = INITIAL_BALL_SIZE
        stim.size = ballSize
        
        # pump balloon
        while continuePumping and not pop:

            # increases ball size with each pump
            ballSize = (
                INITIAL_BALL_SIZE[0] + BALL_TEXTURE_SIZE[0] * increase,
                INITIAL_BALL_SIZE[1] + BALL_TEXTURE_SIZE[1] * increase
            )

            drawTrial(ballSize, trial['balloon_img'], lastTempBank, permBank)

            # process response
            respond = event.waitKeys(
                keyList=[KEY_PUMP, KEY_NEXT, KEY_QUIT],
                maxWait=15
            )

            # no response - continue to next balloon
            if not respond:
                drawText(
                    text, (0, 0), ABSENT_MESSAGE, 'center')
                win.flip()
                core.wait(5)
                continuePumping = False

            # escape key pressed
            elif respond[0] == KEY_QUIT:
                return

            # cash out key pressed
            elif respond[0] == KEY_NEXT:                
                lastTempBank = tempBank
                slot_machine.stop()
                slot_machine.play()
                
                # Im bart() nach dem Pumpen (oder nach jedem trial)
                net_client.send_update(nPumps)

                # aninmation: count up to new balance
                newBalance = permBank + tempBank
                while round(permBank, 2) < round(newBalance, 2):
                    permBank += 0.01
                    drawText(text, (0.4, -0.6),
                             'Last Balloon: \n{:.2f} €'.format(tempBank))
                    drawText(text, (0.4, -0.9),
                             'Total Earned:\n{:.2f} €'.format(permBank))
                    win.flip()
                permBank = newBalance
                continuePumping = False

            # pump key pressed
            elif respond[0] == KEY_PUMP:
                nPumps += 1

                # determine whether balloon pops or not
                if random.random() < 1.0 / (trial['maxPumps'] - nPumps):
                    pop_sound.stop()
                    pop_sound.play()
                    showImg(trial['pop_img'], POP_TEXTURE_SIZE)
                    lastTempBank = 0
                    pop = True
                else:
                    tempBank = nPumps*REWARD
                    
                    # increase balloon size to fill up other 80%
                    increase += 0.8 / max(MAX_PUMPS)

            # save list of data in txt file
            dataList = [info['id'], trialNumber,
                        trial['maxPumps'], nPumps, pop, '{:.2f}'.format(permBank)]
            saveData(dataList, 'data.txt')
    subjectList = [info['id'], info['age'], info['gender'], info['date']]
    saveData(subjectList, 'subjects.txt')

    # final information about reward
    drawText(text, (0, 0),
             FINAL_MESSAGE.format(permBank), 'center')
    win.flip()
    core.wait(5)
    return


# ============================================
# QUESTIONNAIRES: AMS + RISK + LOSS AVERSION
# ============================================

def showLikertQuestion(win, question, labels=(1,2,3,4,5)):
    """Clean Likert scale with proper spacing and readable layout."""

    question_stim = visual.TextStim(
        win,
        text=question,
        units='norm',
        pos=(0, 0.35),
        height=0.065,
        wrapWidth=1.6,
        alignText='center',
        color="White"
    )

    option_stims = []
    n = len(labels)
    spacing = 1.0 / (n - 1)

    for idx, l in enumerate(labels):
        x = -0.5 + spacing * idx
        option_stims.append(
            visual.TextStim(
                win,
                text=str(l),
                units='norm',
                pos=(x, -0.05),
                height=0.11,
                color="Yellow",
                alignText='center'
            )
        )

    instr = visual.TextStim(
        win,
        text="Bitte wählen Sie mit den Zahlentasten\n(1=stimme überhaupt nicht zu - 5=stimme voll und ganz zu).",
        units='norm',
        pos=(0, -0.45),
        height=0.06,
        color="White"
    )

    while True:
        win.clearBuffer()
        question_stim.draw()
        for stim in option_stims:
            stim.draw()
        instr.draw()
        win.flip()

        keys = event.waitKeys(keyList=[str(l) for l in labels] + ['escape'])
        if keys[0] == 'escape':
            core.quit()
        return int(keys[0])


def run_AMS_short(win, subj_id):
    """AMS Kurzform (10 Items, Likert 1–5)."""
    items = [
        # HE
        "Es macht mir Spaß, an Problemen zu arbeiten, die für mich ein bisschen schwierig sind.",
        "Ich mag Situationen, in denen ich feststellen kann, wie gut ich bin.",
        "Probleme, die schwierig zu lösen sind, reizen mich.",
        "Mich reizen Situationen, in denen ich meine Fähigkeiten testen kann.",
        "Ich möchte gern vor eine etwas schwierige Arbeit gestellt werden.",
        # FM
        "Es beunruhigt mich, etwas zu tun, wenn ich nicht sicher bin, dass ich es kann.",
        "Auch bei Aufgaben, von denen ich glaube, dass ich sie kann, habe ich Angst zu versagen.",
        "Dinge, die etwas schwierig sind, beunruhigen mich.",
        "Wenn eine Sache etwas schwierig ist, hoffe ich, dass ich es nicht machen muss, weil ich Angst habe, es nicht zu schaffen.",
        "Wenn ich ein Problem nicht sofort verstehe, werde ich ängstlich."
    ]

    responses = []
    for i, item in enumerate(items, start=1):
        resp = showLikertQuestion(win, f"AMS Item {i}:\n{item}")
        responses.append((i, resp))

        saveData([subj_id, "AMS", i, resp], "data.txt")

    return responses


def run_risk_aversion(win, subj_id):
    """Holt–Laury Risk Aversion with clean layout."""
    responses = []

    for p in range(1, 11):

        title = visual.TextStim(
            win,
            text=f"Risikoentscheidung {p}/10",
            units='norm',
            pos=(0, 0.75),
            height=0.065,
            alignText='center'
        )

        intro = visual.TextStim(
            win,
            text="Bitte wählen Sie zwischen zwei Lotterien:",
            units='norm',
            pos=(0, 0.55),
            height=0.055,
            alignText='center'
        )

        lotA = visual.TextStim(
            win,
            text=(
                f"Lotterie A\n\n"
                f"{p}/10  → 2.00 €\n"
                f"{10-p}/10 → 1.60 €"
            ),
            units='norm',
            pos=(-0.45, 0.05),
            height=0.06,
            wrapWidth=0.6,
            alignText='center',
        )

        lotB = visual.TextStim(
            win,
            text=(
                f"Lotterie B\n\n"
                f"{p}/10  → 3.85 €\n"
                f"{10-p}/10 → 0.10 €"
            ),
            units='norm',
            pos=(0.45, 0.05),
            height=0.06,
            wrapWidth=0.6,
            alignText='center',
        )

        instr = visual.TextStim(
            win,
            text="Taste A = Lotterie A     •     Taste B = Lotterie B",
            units='norm',
            pos=(0, -0.55),
            height=0.055,
            color="Yellow"
        )

        while True:
            win.clearBuffer()
            title.draw()
            intro.draw()
            lotA.draw()
            lotB.draw()
            instr.draw()
            win.flip()

            keys = event.waitKeys(keyList=['a', 'b', 'escape'])
            if keys[0] == 'escape':
                core.quit()

            choice = keys[0].upper()
            responses.append((p, choice))
            saveData([subj_id, "RISK", p, choice], "data.txt")
            break

    return responses


def run_loss_aversion(win, subj_id):
    """Loss aversion with centered question and neat layout."""
    losses = [1.00, 1.50, 2.00, 2.50, 3.00, 3.50]
    responses = []

    for i, L in enumerate(losses, start=1):

        title = visual.TextStim(
            win,
            text=f"Loss Aversion {i}/6",
            units='norm',
            pos=(0, 0.75),
            height=0.065,
            alignText='center'
        )

        question = visual.TextStim(
            win,
            text=(
                "Es wird eine Münze geworfen.\n\n"
                f"Kopf  :  -{L:.2f} €\n"
                f"Zahl  :  +3.00 €"
            ),
            units='norm',
            pos=(0, 0.25),
            height=0.06,
            wrapWidth=1.4,
            alignText='center'
        )

        instr = visual.TextStim(
            win,
            text="Taste Y = akzeptieren     •     Taste N = ablehnen",
            units='norm',
            pos=(0, -0.55),
            height=0.055,
            color="Yellow"
        )

        while True:
            win.clearBuffer()
            title.draw()
            question.draw()
            instr.draw()
            win.flip()

            keys = event.waitKeys(keyList=['y', 'n', 'escape'])
            if keys[0] == 'escape':
                core.quit()

            choice = "ACCEPT" if keys[0] == 'y' else "REJECT"
            responses.append((i, L, choice))
            saveData([subj_id, "LOSS", i, L, choice], "data.txt")
            break

    return responses


def main():
    # dialog for subject information
    infoDlg = showInfoBox()
    info = infoDlg.dictionary
    server_ip = info['server_ip']
    if infoDlg.OK:
        net_client = NetworkClient(info["id"], server_ip)
        # practice rounds
        bart_practice(info, net_client)
        # start experiment
        bart(info, net_client)

        # Netzwerkverbindung schließen (optional, aber sauber)
        net_client.close()

        # ---------------------------
        # NACH DEM BART: FRAGEBÖGEN
        # ---------------------------
        
        center_text = visual.TextStim(
            win,
            text="Bitte beantworten Sie nun einige abschließende Fragebögen.",
            color="White",
            height=0.08,
            pos=(0, 0),
            alignText='center',
            units='norm'
        )
        center_text.draw()
        win.flip()
        core.wait(3)

        # AMS Kurzform
        run_AMS_short(win, info['id'])

        # Risk Aversion (Holt–Laury)
        run_risk_aversion(win, info['id'])

        # Loss Aversion
        run_loss_aversion(win, info['id'])

        final_screen = visual.TextStim(
            win,
            text="Vielen Dank für Ihre Teilnahme!",
            color="White",
            height=0.1,
            pos=(0, 0),
            units='norm'
        )

        final_screen.draw()
        win.flip()
        core.wait(4)

    # quit experiment
    win.close()
    core.quit()


if __name__ == "__main__":
    main()
