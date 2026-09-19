from flask_wtf import FlaskForm
from wtforms import StringField,SelectField,IntegerField,DateTimeField,SubmitField
from wtforms.validators import DataRequired,Email,Optional,NumberRange
class CreateUserForm(FlaskForm):
 email=StringField("Email",validators=[DataRequired(),Email()]);full_name=StringField("Full name",validators=[DataRequired()]);phone=StringField("Phone",validators=[Optional()]);role=SelectField("Role",choices=[("ADMIN","Administrator"),("TEACHER","Teacher"),("HEADMASTER","Headmaster"),("SISO","SISO / Education Authority")],validators=[DataRequired()]);staff_id=StringField("Staff ID",validators=[Optional()]);submit=SubmitField("Create user")
class ClassForm(FlaskForm):
 name=StringField("Class name",validators=[DataRequired()]);submit=SubmitField("Add class")
class SubjectForm(FlaskForm):
 name=StringField("Subject name",validators=[DataRequired()]);submit=SubmitField("Add subject")
class AcademicYearForm(FlaskForm):
 label=StringField("Academic year (e.g. 2026/2027)",validators=[DataRequired()]);submit=SubmitField("Add academic year")
class TermForm(FlaskForm):
 academic_year_id=SelectField("Academic year",coerce=str,validators=[DataRequired()]);name=StringField("Term name (e.g. Term 1)",validators=[DataRequired()]);submit=SubmitField("Add term")
class DeadlineForm(FlaskForm):
 term_id=SelectField("Term",coerce=str,validators=[DataRequired()]);week=IntegerField("Week",validators=[DataRequired(),NumberRange(min=1,max=52)]);due_at=DateTimeField("Due date/time",format="%Y-%m-%d %H:%M",validators=[DataRequired()]);submit=SubmitField("Add deadline")
class TeacherAssignmentForm(FlaskForm):
 teacher_id=SelectField("Teacher",coerce=str,validators=[DataRequired()]);subject_id=SelectField("Subject",coerce=str,validators=[DataRequired()]);class_id=SelectField("Class",coerce=str,validators=[DataRequired()]);academic_year_id=SelectField("Academic year",coerce=str,validators=[DataRequired()]);term_id=SelectField("Term",coerce=str,validators=[Optional()]);submit=SubmitField("Assign")
class WorkflowSettingsForm(FlaskForm):
 current_academic_year_id=SelectField("Current academic year",coerce=str,validators=[Optional()]);current_term_id=SelectField("Current term",coerce=str,validators=[Optional()]);submit=SubmitField("Save settings")
class SchoolForm(FlaskForm):
 school_name=StringField("School name",validators=[DataRequired()]);school_code=StringField("School code",validators=[DataRequired()]);circuit=StringField("Circuit",validators=[Optional()]);district=StringField("District",validators=[Optional()]);submit=SubmitField("Add school")
class SISOAssignmentForm(FlaskForm):
 siso_id=SelectField("SISO",coerce=str,validators=[DataRequired()]);school_id=SelectField("School",coerce=str,validators=[DataRequired()]);academic_year_id=SelectField("Academic year",coerce=str,validators=[DataRequired()]);submit=SubmitField("Assign school")
