from flask import Blueprint, jsonify, request
from models.database import FollowUp, db

followup_bp = Blueprint('followup_bp', __name__)

@followup_bp.route('/api/followups/<int:contact_id>', methods=['GET'])
def get_followups(contact_id):
    followups = FollowUp.query.filter_by(contact_id=contact_id).order_by(FollowUp.created_at.desc()).all()
    return jsonify([
        {
            'id': f.id,
            'tag': f.tag,
            'note': f.note,
            'created_at': f.created_at.isoformat() if f.created_at else None,
            'updated_at': f.updated_at.isoformat() if f.updated_at else None
        } for f in followups
    ])

@followup_bp.route('/api/followups/<int:contact_id>', methods=['POST'])
def add_followup(contact_id):
    data = request.get_json()
    tag = data.get('tag', '')
    note = data.get('note', '')
    followup = FollowUp(contact_id=contact_id, tag=tag, note=note)
    db.session.add(followup)
    db.session.commit()
    return jsonify({'success': True, 'id': followup.id})

@followup_bp.route('/api/followups/<int:followup_id>', methods=['PUT'])
def update_followup(followup_id):
    data = request.get_json()
    followup = FollowUp.query.get_or_404(followup_id)
    followup.tag = data.get('tag', followup.tag)
    followup.note = data.get('note', followup.note)
    db.session.commit()
    return jsonify({'success': True})

@followup_bp.route('/api/followups/<int:followup_id>', methods=['DELETE'])
def delete_followup(followup_id):
    followup = FollowUp.query.get_or_404(followup_id)
    db.session.delete(followup)
    db.session.commit()
    return jsonify({'success': True})
