from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional


class NewPlanForm(FlaskForm):
    academic_year_id = SelectField("Academic year", coerce=str, validators=[DataRequired()])
    term_id = SelectField("Term", coerce=str, validators=[DataRequired()])
    week = IntegerField("Week", validators=[DataRequired(), NumberRange(min=1, max=20)])
    class_id = SelectField("Class", coerce=str, validators=[DataRequired()])
    subject_id = SelectField("Subject", coerce=str, validators=[DataRequired()])
    submit = SubmitField("Create draft")


class PlanContentForm(FlaskForm):
    topic = StringField("Topic/Strand", validators=[DataRequired()])
    sub_strand = StringField("Sub-strand", validators=[Optional()])
    content_standard = TextAreaField("Content standard", validators=[DataRequired()])
    indicator = TextAreaField("Indicator/performance indicator", validators=[DataRequired()])
    learning_objectives = TextAreaField("Learning objectives", validators=[DataRequired()])
    resources = TextAreaField("Teaching and learning resources", validators=[Optional()])
    activities = TextAreaField("Teaching and learning activities", validators=[DataRequired()])
    assessment = TextAreaField("Assessment activities", validators=[Optional()])
    references_text = TextAreaField("References", validators=[Optional()])
    remarks = TextAreaField("Remarks", validators=[Optional()])
    save_draft = SubmitField("Save as draft")
    submit_for_review = SubmitField("Submit for review")


class UploadForm(FlaskForm):
    document = FileField(
        "Learner plan document",
        validators=[FileAllowed(["pdf", "doc", "docx"], "PDF, DOC, and DOCX only.")],
    )
    upload = SubmitField("Upload document")
