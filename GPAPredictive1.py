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
    if percent >= 90: return 4.0
    if percent >= 80: return 3.0
    if percent >= 70: return 2.0
    if percent >= 60: return 1.0
    return 0.0

def calculate_predicted(data: dict) -> float:
    predicted_score = 0
    for cat, info in data.items():
        if cat == "Credits":
            continue
        percent = info["percent"]
        if cat == "Participation":
            v = info.get("value", 0)
            predicted_score += (float(v) / 100) * percent
        elif cat in ["Assignments", "Quiz"]:
            done = info.get("done", 0)
            failed = info.get("failed", 0)
            total = info.get("total") or info.get("amount", 0)
            if total > 0:
                vals = []
                for i in range(total):
                    if done > 0:
                        vals.append(100); done -= 1
                    elif failed > 0:
                        vals.append(0); failed -= 1
                    else:
                        vals.append(50)
                predicted_score += (sum(vals) / len(vals)) / 100 * percent
        elif cat == "MidTerm":
            tests = [info.get("test1"), info.get("test2")]
            tests = [float(x) for x in tests if x is not None]
            avg = sum(tests) / len(tests) if tests else 50
            predicted_score += (avg / 100) * percent
        elif cat == "Final":
            v = info.get("value", 30)
            predicted_score += (float(v) / 100) * percent
    return round(predicted_score, 2)

def calculate_overall_gpa(user_subjects_data: dict) -> float | None:
    total_credits = 0
    total_points = 0
    for subj, data in user_subjects_data.items():
        if "Credits" not in data:
            continue
        credits = data["Credits"]
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
            TextInput(label="Participation Percentage", custom_id="participation_percent", style=TextInputStyle.short, required=True),
            TextInput(label="Completed (%)", custom_id="participation_value", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Participation", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        percent = inter.text_values["participation_percent"]
        value = inter.text_values["participation_value"]
        await inter.response.send_message(f"✅ Participation saved for {subj} ({value}% of {percent}%)", ephemeral=True)


class ModalAssignments(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Assignments Percentage", custom_id="assignments_percent", style=TextInputStyle.short, required=True),
            TextInput(label="Total Assignments", custom_id="assignments_total", style=TextInputStyle.short, required=True),
            TextInput(label="Completed Assignments", custom_id="assignments_done", style=TextInputStyle.short, required=True),
            TextInput(label="Failed Assignments", custom_id="assignments_failed", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Assignments", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        done = inter.text_values["assignments_done"]
        total = inter.text_values["assignments_total"]
        await inter.response.send_message(f"✅ Assignments saved for {subj} ({done}/{total})", ephemeral=True)


class ModalQuiz(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Quiz Percentage", custom_id="quiz_percent", style=TextInputStyle.short, required=True),
            TextInput(label="Total Quizzes", custom_id="quiz_amount", style=TextInputStyle.short, required=True),
            TextInput(label="Completed Quizzes", custom_id="quiz_done", style=TextInputStyle.short, required=True),
            TextInput(label="Failed Quizzes", custom_id="quiz_failed", style=TextInputStyle.short, required=True)
        ]
        super().__init__(title="Quiz", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        done = inter.text_values["quiz_done"]
        total = inter.text_values["quiz_amount"]
        await inter.response.send_message(f"✅ Quiz saved for {subj} ({done}/{total})", ephemeral=True)

class ModalMidTerm(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Mid-Term Percentage", custom_id="mid_percent", style=TextInputStyle.short, required=True),
            TextInput(label="Mid-Term 1 (%)", custom_id="mid_test1", style=TextInputStyle.short, required=True),
            TextInput(label="Mid-Term 2 (%) (optional)", custom_id="mid_test2", style=TextInputStyle.short, required=False)
        ]
        super().__init__(title="Mid-Term", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        test1 = inter.text_values["mid_test1"]
        test2 = inter.text_values["mid_test2"] or "N/A"
        await inter.response.send_message(f"✅ Mid-Term saved for {subj} (Test1: {test1}, Test2: {test2})", ephemeral=True)

class ModalFinal(Modal):
    def __init__(self):
        components = [
            TextInput(label="Subject Name", custom_id="subject", style=TextInputStyle.short, required=True),
            TextInput(label="Final Percentage", custom_id="final_percent", style=TextInputStyle.short, required=True),
            TextInput(label="Final Test (%)", custom_id="final_test", style=TextInputStyle.short, required=False)
        ]
        super().__init__(title="Final Test", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subj = inter.text_values["subject"]
        value = inter.text_values["final_test"] or "N/A"
        await inter.response.send_message(f"✅ Final saved for {subj} (Score: {value})", ephemeral=True)

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
        await inter.response.send_message(f"✅ Credits saved for {subj} ({credits})", ephemeral=True)
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
            avg = calculate_predicted(data)
            results.append(f"{subj}: Predicted {avg:.2f}")
        gpa_pred = calculate_overall_gpa(user)
        if gpa_pred is not None:
            results.append(f"GPA: {gpa_pred:.2f}")
        await inter.response.send_message("\n".join(results), ephemeral=True)

@bot.slash_command(description="Buttons")
async def menu(inter):
    await inter.response.send_message("Select:", view=MyView())

bot.run("MTQxNTIzMjE0NjE1ODc4MDQyNg.GWjcki.6UGo2t6ob-VxuhWTK0rh7FW9PJcs3yd0UMxkLc")
