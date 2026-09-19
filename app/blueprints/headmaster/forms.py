from flask_wtf import FlaskForm
from wtforms import TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class ApproveForm(FlaskForm):
    confirm = BooleanField("I confirm I want to approve this learner plan", validators=[DataRequired(message="Please check the confirmation box to approve.")])
    submit = SubmitField("Approve plan")

class RejectForm(FlaskForm):
    reason = TextAreaField("Reason for rejection", validators=[DataRequired()])
    submit = SubmitField("Reject plan")

class RequestCorrectionForm(FlaskForm):
    comment = TextAreaField("Reason for correction", validators=[DataRequired()])
    submit = SubmitField("Request correction")
