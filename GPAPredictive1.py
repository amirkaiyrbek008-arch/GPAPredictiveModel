import disnake
from disnake.ext import commands
from disnake.ui import Modal, TextInput
from disnake import TextInputStyle

bot = commands.InteractionBot()
user_data = {}

def get_user(inter):
    if inter.author.id not in user_data:
        user_data[inter.author.id] = {}
    return user_data[inter.author.id]

def percent_to_grade_point(percent: float) -> float:
    if percent >= 95: 
        return 4.0
    if percent >= 90:
        return 3.75
    if percent >= 85: 
        return 3.5
    if percent >= 80:
        return 3.0
    if percent >= 75:
        return 2.5
    if percent >= 70: 
        return 2.0
    if percent >= 65:
        return 1.5
    if percent >= 60: 
        return 1.0
    return 0.0

def calculate_predicted(data: dict) -> float:
    predicted_score = 0
    avg = []
    for key, info in data.items():
        if key == "Credits":
            continue
        percent = info["percent"]
        if key == "Participation":
            v = info.get("value", 0)
            predicted_score += v * percent/100
            avg.append(v)
        elif key in ["Assignments", "Quiz"]:
            total = info.get("total")
            done = info.get("done", 0)
            failed = info.get("failed", 0)
            ongoing = total - failed
            d = 0
            f = 0
            if total > 0 and (done > 0 or failed > 0):
                    pattern = [1] * done + [0] * failed 
                    idx = 0
                    for i in range(total):
                        if pattern[idx] == 1:
                            d += 1
                        else:
                            f += 1
                        idx = (idx + 1) % len(pattern)
            predicted_score += (d/total) * percent
            avg.append(d/total * 100)
        elif key == "Mid-Term":
            if info["test1"] == "n" and info["test2"] == "n":
                predicted_score += (sum(avg)/len(avg)) * (percent*2)
                avg.append(sum(avg)/len(avg))
            elif info["test1"] == "n":
                score = int(info["test2"])
                predicted_score += (score / 100) * percent*2
                avg.append(score)
            elif info["test2"] == "n":
                score = int(info["test1"])
                predicted_score += (score / 100) * percent*2
                avg.append(score)
            else:
                predicted_score += (int(info["test1"]) + int(info["test2"]))/200 * percent
                avg.append((int(info["test1"]) + int(info["test2"]))/2)
        elif key == "Final":
            v = info.get("value", predicted_score)
            if v == 'n':
                predicted_score += ((sum(avg)/len(avg)) * float(percent))/100
            else:
                predicted_score += (int(v) / 100) * float(percent)
    return round(predicted_score, 2)

def calculate_overall_gpa(user_subjects_data: dict) -> float | None:
    total_credits = 0
    total_points = 0
    for subj, data in user_subjects_data.items():
        if "Credits" not in data:
            continue
        credits = float(data.get("value", 0))
        total_credits += credits
        avg_grade = calculate_predicted(data)
        total_points += percent_to_grade_point(avg_grade) * credits
    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)

class ModalParticipation(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Participation Percentage", custom_id="percent", style=TextInputStyle.short, required=True),
            TextInput(label="Completed (%)", custom_id="value", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Participation", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        percent = float(inter.text_values["percent"])
        value = float(inter.text_values["value"])

        user = get_user(inter)
        if subj not in user:
            user[subj] = {}

        user[subj]["Participation"] = {
            "percent": percent,
            "value": value
        }

        await inter.response.send_message(
            f"Participation saved for {subj}", 
            ephemeral=True
        )

class ModalAssignments(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Assignments Percentage", custom_id="percent", style=TextInputStyle.short, required=True),
            TextInput(label="Total Assignments", custom_id="total", style=TextInputStyle.short, required=True),
            TextInput(label="Completed Assignments", custom_id="done", style=TextInputStyle.short, required=True),
            TextInput(label="Failed Assignments", custom_id="failed", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Assignments", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        percent = float(inter.text_values["percent"])
        total = int(inter.text_values["total"])
        done = int(inter.text_values["done"])
        failed = int(inter.text_values["failed"])

        user = get_user(inter)
        if subj not in user:
            user[subj] = {}

        user[subj]["Assignments"] = {
            "percent": percent,
            "total": total,
            "done": done,
            "failed": failed
        }

        await inter.response.send_message(
            f"Assignments saved for {subj} ({done}/{total})", 
            ephemeral=True
        )


class ModalQuiz(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Quiz Percentage", custom_id="percent", style=TextInputStyle.short, required=True),
            TextInput(label="Total Quizzes", custom_id="total", style=TextInputStyle.short, required=True),
            TextInput(label="Completed Quizzes", custom_id="done", style=TextInputStyle.short, required=True),
            TextInput(label="Failed Quizzes", custom_id="failed", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Quiz", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        percent = float(inter.text_values["percent"])
        total = int(inter.text_values["total"])
        done = int(inter.text_values["done"])
        failed = int(inter.text_values["failed"])

        user = get_user(inter)
        if subj not in user:
            user[subj] = {}

        user[subj]["Quiz"] = {
            "percent": percent,
            "total": total,
            "done": done,
            "failed": failed
        }

        await inter.response.send_message(
            f"Quiz saved for {subj} ({done}/{total})", 
            ephemeral=True
        )


class ModalMidTerm(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Mid-Term Percentage", custom_id="percent", style=TextInputStyle.short, required=True),
            TextInput(label="Mid-Term 1 (%, or n if you don't have", custom_id="test1", style=TextInputStyle.short, required=True),
            TextInput(label="Mid-Term 2 (%, or n if you don't have", custom_id="test2", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Mid-Term", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        percent = float(inter.text_values["percent"])
        test1 = inter.text_values["test1"]
        test2 = inter.text_values["test2"]

        user = get_user(inter)
        if subj not in user:
            user[subj] = {}

        user[subj]["Mid-Term"] = {
            "percent": percent,
            "test1": test1,
            "test2": test2
        }

        await inter.response.send_message(
            f"Mid-Term Tests saved for {subj} (Test 1 - {test1}| Test 2 - {test2})", 
            ephemeral=True
        )

class ModalFinal(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Final Percentage", custom_id="percent", style=TextInputStyle.short, required=True),
            TextInput(label="Final Test (%, or n if you don't have)", custom_id="final", style=TextInputStyle.short, required=False)
        ]
        super().__init__(title="Final", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        percent = inter.text_values["percent"]
        value = inter.text_values["final"]

        user = get_user(inter)
        if subj not in user:
            user[subj] = {}

        user[subj]["Final"] = {
            "percent": percent,
            "value": value 
            }
        await inter.response.send_message(f"Final saved for {subj} (Score: {value})", ephemeral=True)


class ModalCredits(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Credits", custom_id="credits", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Credits", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        credits = inter.text_values["credits"]

        user = get_user(inter)
        if subj not in user:
            user[subj] = {}

        user[subj]["Credits"] = {
            "Credits": credits
        }
        await inter.response.send_message(f"Credits saved for {subj} ({credits})", ephemeral=True)
class MyView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @disnake.ui.button(label="Participation", style=disnake.ButtonStyle.primary)
    async def participation(self, _, inter): await inter.response.send_modal(ModalParticipation())
    @disnake.ui.button(label="Assignments", style=disnake.ButtonStyle.primary)
    async def assignments(self, _, inter): await inter.response.send_modal(ModalAssignments())
    @disnake.ui.button(label="Quiz", style=disnake.ButtonStyle.primary)
    async def quiz(self, _, inter): await inter.response.send_modal(ModalQuiz())
    @disnake.ui.button(label="Mid-Term", style=disnake.ButtonStyle.primary)
    async def midterm(self, _, inter): await inter.response.send_modal(ModalMidTerm())
    @disnake.ui.button(label="Final", style=disnake.ButtonStyle.primary)
    async def final(self, _, inter): await inter.response.send_modal(ModalFinal())
    @disnake.ui.button(label="Credits", style=disnake.ButtonStyle.secondary)
    async def credits(self, _, inter): await inter.response.send_modal(ModalCredits())
    @disnake.ui.button(label="Calculate", style=disnake.ButtonStyle.success)
    async def calculate(self, _, inter):
        user = get_user(inter)
        results = []

        for subj, data in user.items():
            avg_grade = calculate_predicted(data)
            results.append(
                f" {subj}:\n"
                f"  Predicted Procents: {avg_grade:.2f}"
                f"  Predicted Grade Point: {percent_to_grade_point(avg_grade)}"
            )

        gpa_pred = calculate_overall_gpa(user)
        if gpa_pred is not None:
            results.append(
                f"\n GPA:\n"
                f"  Predicted GPA: {gpa_pred:.2f}"
            )

        if results:
            await inter.response.send_message("\n".join(results), ephemeral=True)
        else:
            await inter.response.send_message("]\Нет данных для расчёта", ephemeral=True)

@bot.slash_command(description="Buttons")
async def menu(inter):
    await inter.response.send_message("Select:", view=MyView())
bot.run("TOKEN")
