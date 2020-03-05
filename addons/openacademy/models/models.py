# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, exceptions


class Course(models.Model):
    """
    Courses
    """
    _name = 'openacademy.course'
    _description = 'OpenAcademy Courses'

    name = fields.Char(string='Title', required=True)
    description = fields.Text()

    responsible_id = fields.Many2one('res.users',
                                     ondelete='set null', string='Responsible', index=True)
    
    session_ids = fields.One2many('openacademy.session', 'course_id', string='Sessions')


    # Copies this session under a name 'Copy of <number of copies>'
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u'Copy of {}'.format(self.name))])
        if not copied_count:
            new_name = u'Copy of {}'.format(self.name)
        else:
            new_name = u'Copy of {} ({})'.format(self.name, copied_count)
        default['name'] = new_name
        return super(Course, self).copy(default)

    # SQL constraints to check if description and title are different and
    # if the title is unique
    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         'The title of the course should not be the description'),

        ('name_unique',
         'UNIQUE(name)',
         'The course title must be unique'),
    ]

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for record in self:
            if not (record.start_date and record.duration):
                record.end_date = record.start_date
                continue
            duration = timedelta(days=record.duration - 1)
            record.end_date = record.start_date + duration
    
    def _set_end_date(self):
        for record in self:
            if not (record.start_date and record.end_date):
                continue

            record.duration = (record.end_date - record.start_date).days + 1

class Session(models.Model):
    """
    Sessions of individual courses
    """
    _name = 'openacademy.session'
    _description = 'Openacademy Sessions'

    name = fields.Char(required=True)
    color = fields.Integer()

    active = fields.Boolean(default=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help='Duration in days')
    end_date = fields.Date(string='End Date', store=True,
        compute='_get_end_date', inverse='_set_end_date')

    instructor_id = fields.Many2one('res.partner', string='Instructor',
        domain=['|', ('instructor', '=', True),
            ('category_id.name', 'ilike', 'Teacher')])
    course_id = fields.Many2one('openacademy.course',
                                    ondelete='cascade', string='Course', required=True)
    attendee_ids = fields.Many2many('res.partner', string='Attendees')

    attendees_count = fields.Integer(
        string='Attendees count', compute='_get_attendees_count', store=True)
    seats = fields.Integer(string='Number of seats')
    

    # Computed field - percentage of taken seats
    taken_seats = fields.Float(string='Taken seats', compute='_taken_seats')

    # Computes the percentage of taken seats at a session
    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for record in self:
            if not record.seats:
                record.taken_seats = 0.0
            else:
                record.taken_seats = 100.0 * len(record.attendee_ids) / record.seats
    
    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for record in self:
            record.attendees_count = len(record.attendee_ids)
    

    # Verifies the validity of changes to seats and attendees
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': 'The number of available seats may not be negative',
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': 'Too many attendees',
                    'message': 'Increase seats or remove excess attendees',
                },
            }
    
    # Verifies that the instructor is not also an attendee
    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for record in self:
            if record.instructor_id and record.instructor_id in record.attendee_ids:
                raise exceptions.ValidationError(
                    "A session's instructor can't be an attendee")
