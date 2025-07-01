from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from models.database import db, Opportunity, Task, Contact, Activity, User
from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta
import json

crm_bp = Blueprint('crm_bp', __name__)

@crm_bp.route('/crm')
def crm_panel():
    estados = ['Nuevo', 'En seguimiento', 'Oportunidad', 'Cerrado', 'Obsoleto']
    # Filtros desde query params
    name_filter = request.args.get('name', '').strip()
    rubro_filter = request.args.get('rubro', '').strip()
    
    # Crear oportunidades automáticamente para clientes con calificación >= 75 que no tengan oportunidad
    clientes_destacados = Contact.query.filter(Contact.quality_score >= 75).all()
    for cliente in clientes_destacados:
        existe = Opportunity.query.filter_by(contact_id=cliente.id).first()
        if not existe:
            nueva_opp = Opportunity(
                contact_id=cliente.id, 
                estado='Nuevo',
                canal_origen='Auto-generado',
                probabilidad=30
            )
            db.session.add(nueva_opp)
            db.session.commit()  # Commit para obtener el id
            # Registrar actividad SOLO después del commit
            actividad = Activity(
                opportunity_id=nueva_opp.id,
                tipo='creacion',
                descripcion='Oportunidad creada automáticamente por calificación alta',
                usuario='Sistema'
            )
            db.session.add(actividad)
            db.session.commit()
    
    # Configuración de paginación
    oportunidades_por_pagina = 5  # Cargar inicialmente solo 5 oportunidades por columna
    
    # Cargar oportunidades por estado con filtros y paginación
    oportunidades = {}
    totales_por_estado = {}
    for estado in estados:
        query = Opportunity.query.options(
            joinedload(Opportunity.contact),
            joinedload(Opportunity.tareas),
            joinedload(Opportunity.actividades)
        ).filter_by(estado=estado)
        if name_filter:
            query = query.join(Opportunity.contact).filter(Contact.name.ilike(f'%{name_filter}%'))
        if rubro_filter:
            query = query.join(Opportunity.contact).filter(Contact.search_query.ilike(f'%{rubro_filter}%'))
        
        # Obtener total para mostrar contador
        totales_por_estado[estado] = query.count()
        
        # Ordenar oportunidades por última actividad, poniendo las que no tienen fecha al final
        oportunidades[estado] = query.order_by(
            Opportunity.ultima_actividad.is_(None),
            desc(Opportunity.ultima_actividad)
        ).limit(oportunidades_por_pagina).all()
    
    # Obtener métricas para el dashboard
    total_oportunidades = Opportunity.query.count()
    oportunidades_activas = Opportunity.query.filter(Opportunity.estado.notin_(['Cerrado', 'Obsoleto'])).count()
    valor_total = db.session.query(func.sum(Opportunity.valor_estimado)).filter(Opportunity.estado.notin_(['Obsoleto'])).scalar() or 0
    tareas_pendientes = Task.query.filter_by(completada=False).count()
    
    # Métricas por estado
    metricas_estado = {}
    for estado in estados:
        count = Opportunity.query.filter_by(estado=estado).count()
        valor = db.session.query(func.sum(Opportunity.valor_estimado)).filter(Opportunity.estado == estado).scalar() or 0
        metricas_estado[estado] = {'count': count, 'valor': valor}
    
    return render_template('crm.html', 
                         oportunidades=oportunidades, 
                         estados=estados,
                         total_oportunidades=total_oportunidades,
                         oportunidades_activas=oportunidades_activas,
                         valor_total=valor_total,
                         tareas_pendientes=tareas_pendientes,
                         metricas_estado=metricas_estado,                         totales_por_estado=totales_por_estado,
                         oportunidades_por_pagina=oportunidades_por_pagina)

@crm_bp.route('/crm/cargar_mas_oportunidades')
def cargar_mas_oportunidades():
    """Cargar más oportunidades para una columna específica del Kanban"""
    estado = request.args.get('estado', '')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 5))
    name_filter = request.args.get('name', '').strip()
    rubro_filter = request.args.get('rubro', '').strip()
    
    if not estado:
        return jsonify({'error': 'Estado requerido'}), 400
    
    # Construir query con filtros
    query = Opportunity.query.options(
        joinedload(Opportunity.contact),
        joinedload(Opportunity.tareas),
        joinedload(Opportunity.actividades)
    ).filter_by(estado=estado)
    
    if name_filter:
        query = query.join(Opportunity.contact).filter(Contact.name.ilike(f'%{name_filter}%'))
    if rubro_filter:
        query = query.join(Opportunity.contact).filter(Contact.search_query.ilike(f'%{rubro_filter}%'))
    
    # Obtener oportunidades con paginación
    oportunidades = query.order_by(
        Opportunity.ultima_actividad.is_(None),
        desc(Opportunity.ultima_actividad)
    ).offset(offset).limit(limit).all()
      # Renderizar las tarjetas como HTML parcial
    from flask import render_template_string
    
    template = '''
    {% for opp in oportunidades %}
    <div class="kanban-card">
        <div class="priority-indicator priority-{{ opp.prioridad|lower if opp.prioridad else 'baja' }}"></div>
        
        <div class="contact-name">{{ opp.contact.name|clean_text }}</div>
        
        <div class="contact-info">
            {% if opp.contact.email %}
            <div class="contact-detail">
                <i class="fas fa-envelope"></i>
                <a href="mailto:{{ opp.contact.email }}">{{ opp.contact.email }}</a>
            </div>
            {% endif %}
            {% if opp.contact.phone %}
            <div class="contact-detail">
                <i class="fas fa-phone"></i>
                <a href="tel:{{ opp.contact.phone }}">{{ opp.contact.phone }}</a>
            </div>
            {% endif %}
            {% if opp.contact.location %}
            <div class="contact-detail">
                <i class="fas fa-map-marker-alt"></i>
                <span>{{ opp.contact.location }}</span>
            </div>
            {% endif %}
        </div>
        
        {% if opp.valor_estimado and opp.valor_estimado > 0 %}
        <div class="valor-estimado">
            💰 ${{ "{:,.0f}".format(opp.valor_estimado) }}
            <span class="probabilidad-badge">{{ opp.probabilidad }}%</span>
        </div>
        {% endif %}
        
        <div class="last-contact">
            <i class="fas fa-clock me-1"></i>
            Última actividad: {{ opp.ultima_actividad.strftime('%d/%m/%Y %H:%M') if opp.ultima_actividad else 'Sin actividad' }}
        </div>
        
        {% if opp.tareas %}
        <div class="task-summary">
            {% set tareas_pendientes = opp.tareas|selectattr('completada', 'equalto', false)|list|length %}
            {% set tareas_completadas = opp.tareas|selectattr('completada', 'equalto', true)|list|length %}
            <i class="fas fa-tasks me-1"></i>
            <span class="task-pending">{{ tareas_pendientes }} pendientes</span>
            <span class="task-completed">• {{ tareas_completadas }} completadas</span>
        </div>
        {% endif %}
        
        <div class="accordion-section">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                <i class="fas fa-cog me-1"></i>Gestión Rápida
                <i class="fas fa-chevron-down float-end"></i>
            </div>
            <div class="accordion-content" style="display: none;">
                <div class="d-flex gap-2 mt-2">
                    <a href="{{ url_for('crm_bp.detalle_oportunidad', opp_id=opp.id) }}" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-eye"></i> Ver detalle
                    </a>
                    <button class="btn btn-outline-success btn-sm" onclick="abrirModalTarea({{ opp.id }})">
                        <i class="fas fa-plus"></i> Tarea
                    </button>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
    '''
    
    html_cards = render_template_string(template, oportunidades=oportunidades)
    
    return jsonify({
        'html': html_cards,
        'count': len(oportunidades),
        'has_more': len(oportunidades) == limit
    })

@crm_bp.route('/crm/kanban_data')
def crm_kanban_data():
    estados = ['Nuevo', 'En seguimiento', 'Oportunidad', 'Cerrado', 'Obsoleto']
    name_filter = request.args.get('name', '').strip()
    rubro_filter = request.args.get('rubro', '').strip()
    
    # Configuración de paginación para filtros
    oportunidades_por_pagina = 5
    
    oportunidades = {}
    totales_por_estado = {}
    for estado in estados:
        query = Opportunity.query.options(
            joinedload(Opportunity.contact),
            joinedload(Opportunity.tareas),
            joinedload(Opportunity.actividades)
        ).filter_by(estado=estado)
        
        if name_filter:
            query = query.join(Opportunity.contact).filter(Contact.name.ilike(f'%{name_filter}%'))
        if rubro_filter:
            query = query.join(Opportunity.contact).filter(Contact.search_query.ilike(f'%{rubro_filter}%'))
        
        # Obtener total para mostrar contador
        totales_por_estado[estado] = query.count()
        
        # Limitar a las primeras oportunidades para la vista inicial
        oportunidades[estado] = query.order_by(
            Opportunity.ultima_actividad.is_(None),
            desc(Opportunity.ultima_actividad)
        ).limit(oportunidades_por_pagina).all()
    
    # Renderizar solo el tablero Kanban como HTML parcial
    return render_template('kanban_partial.html', 
                         oportunidades=oportunidades, 
                         estados=estados,
                         totales_por_estado=totales_por_estado,
                         oportunidades_por_pagina=oportunidades_por_pagina)

@crm_bp.route('/crm/nota/<int:opp_id>', methods=['POST'])
def agregar_nota(opp_id):
    nota = request.form['nota']
    opp = Opportunity.query.get(opp_id)
    if opp:
        opp.nota = nota
        opp.ultima_actividad = datetime.utcnow()
        
        # Registrar actividad
        actividad = Activity(
            opportunity_id=opp_id,
            tipo='nota',
            descripcion='Nota agregada/actualizada',
            usuario=request.form.get('usuario', 'Usuario'),
            detalles={'nota': nota}
        )
        db.session.add(actividad)
        db.session.commit()
        flash('Nota agregada correctamente', 'success')
    return redirect(url_for('crm_bp.crm_panel'))

@crm_bp.route('/crm/tarea/<int:opp_id>', methods=['POST'])
def agregar_tarea(opp_id):
    descripcion = request.form['descripcion']
    fecha_vencimiento = request.form.get('fecha_vencimiento')
    prioridad = request.form.get('prioridad', 'Media')
    tipo = request.form.get('tipo', 'General')
    asignado_a_id = request.form.get('asignado_a_id')
      # Convertir asignado_a_id a entero si no está vacío
    if asignado_a_id and asignado_a_id.strip():
        try:
            asignado_a_id = int(asignado_a_id)
        except ValueError:
            asignado_a_id = None
    else:
        asignado_a_id = None
    
    tarea = Task(
        opportunity_id=opp_id, 
        descripcion=descripcion,
        prioridad=prioridad,
        tipo=tipo,
        asignado_a_id=asignado_a_id,
        completada=False,  # Asegurar que la tarea inicie como pendiente
        fecha_vencimiento=datetime.strptime(fecha_vencimiento, '%Y-%m-%d') if fecha_vencimiento else None
    )
    db.session.add(tarea)
    
    # Actualizar última actividad de la oportunidad
    opp = Opportunity.query.get(opp_id)
    if opp:
        opp.ultima_actividad = datetime.utcnow()
    
    # Obtener el nombre del usuario asignado para la actividad
    usuario_asignado = ''
    if asignado_a_id:
        user = User.query.get(asignado_a_id)
        usuario_asignado = f' - Asignada a: {user.username}' if user else ''
    
    # Registrar actividad
    actividad = Activity(
        opportunity_id=opp_id,
        tipo='tarea_creada',
        descripcion=f'Nueva tarea creada: {descripcion}{usuario_asignado}',
        usuario=request.form.get('usuario', 'Usuario'),
        detalles={'prioridad': prioridad, 'tipo': tipo, 'asignado_a_id': asignado_a_id}
    )
    db.session.add(actividad)
    db.session.commit()
    flash('Tarea agregada correctamente', 'success')
    return redirect(url_for('crm_bp.crm_panel'))

@crm_bp.route('/crm/estado/<int:opp_id>', methods=['POST'])
def cambiar_estado(opp_id):
    nuevo_estado = request.form['estado']
    opp = Opportunity.query.get(opp_id)
    if opp:
        estado_anterior = opp.estado
        opp.estado = nuevo_estado
        opp.ultima_actividad = datetime.utcnow()
        
        # Ajustar probabilidad según el estado
        probabilidades = {
            'Nuevo': 25,
            'En seguimiento': 50,
            'Oportunidad': 75,
            'Cerrado': 100
        }
        opp.probabilidad = probabilidades.get(nuevo_estado, opp.probabilidad)
        
        # Registrar actividad
        actividad = Activity(
            opportunity_id=opp_id,
            tipo='cambio_estado',
            descripcion=f'Estado cambiado de "{estado_anterior}" a "{nuevo_estado}"',
            usuario=request.form.get('usuario', 'Usuario'),
            detalles={'estado_anterior': estado_anterior, 'estado_nuevo': nuevo_estado}
        )
        db.session.add(actividad)
        db.session.commit()
        flash(f'Estado cambiado a {nuevo_estado}', 'success')
    return redirect(url_for('crm_bp.crm_panel'))

@crm_bp.route('/crm/oportunidad/<int:opp_id>/detalle')
def detalle_oportunidad(opp_id):
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Actividades por página
    
    oportunidad = Opportunity.query.options(
        joinedload(Opportunity.contact),
        joinedload(Opportunity.tareas),
        joinedload(Opportunity.actividades)
    ).get(opp_id)
    
    if not oportunidad:
        flash('Oportunidad no encontrada', 'error')
        return redirect(url_for('crm_bp.crm_panel'))
    
    # Limpiar datos de tareas para evitar errores de comparación
    for tarea in oportunidad.tareas:
        # Asegurar que completada sea boolean
        if tarea.completada is None:
            tarea.completada = False
            db.session.add(tarea)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al actualizar tareas: {e}")
    
    # Obtener actividades paginadas
    actividades_paginadas = Activity.query.filter_by(opportunity_id=opp_id)\
        .order_by(desc(Activity.fecha))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Obtener solo las tareas más importantes (últimas 5 + pendientes)
    tareas_pendientes = [t for t in oportunidad.tareas if not t.completada]
    tareas_completadas_recientes = [t for t in oportunidad.tareas if t.completada]
    tareas_completadas_recientes = sorted(tareas_completadas_recientes, 
                                        key=lambda x: x.fecha_completada or x.fecha_creacion, 
                                        reverse=True)[:3]  # Solo las 3 más recientes
    
    tareas_mostrar = tareas_pendientes + tareas_completadas_recientes
    
    return render_template('crm_detalle.html', 
                         oportunidad=oportunidad, 
                         actividades=actividades_paginadas,
                         tareas_mostrar=tareas_mostrar,
                         total_tareas=len(oportunidad.tareas),
                         total_actividades=Activity.query.filter_by(opportunity_id=opp_id).count())

@crm_bp.route('/crm/dashboard')
def dashboard():
    """Dashboard de métricas y estadísticas del CRM"""
    estados = ['Nuevo', 'En seguimiento', 'Oportunidad', 'Cerrado', 'Obsoleto']
    
    # Métricas generales
    total_oportunidades = Opportunity.query.count()
    oportunidades_activas = Opportunity.query.filter(Opportunity.estado.notin_(['Cerrado', 'Obsoleto'])).count()
    oportunidades_cerradas = Opportunity.query.filter_by(estado='Cerrado').count()
    valor_total = db.session.query(func.sum(Opportunity.valor_estimado)).filter(Opportunity.estado.notin_(['Obsoleto'])).scalar() or 0
    valor_pipeline = db.session.query(func.sum(Opportunity.valor_estimado)).filter(Opportunity.estado.notin_(['Cerrado', 'Obsoleto'])).scalar() or 0
    
    # Métricas por estado
    metricas_estado = {}
    for estado in estados:
        count = Opportunity.query.filter_by(estado=estado).count()
        valor = db.session.query(func.sum(Opportunity.valor_estimado)).filter(Opportunity.estado == estado).scalar() or 0
        if count > 0:
            promedio_valor = valor / count if valor > 0 else 0
        else:
            promedio_valor = 0
        metricas_estado[estado] = {
            'count': count, 
            'valor': valor,
            'promedio': promedio_valor
        }
    
    # Top 10 oportunidades por valor
    top_oportunidades = Opportunity.query.options(joinedload(Opportunity.contact))\
        .filter(Opportunity.valor_estimado > 0)\
        .filter(Opportunity.estado.notin_(['Obsoleto']))\
        .order_by(desc(Opportunity.valor_estimado))\
        .limit(10).all()
      # Tareas por estado
    tareas_pendientes = Task.query.filter_by(completada=False).count()
    tareas_completadas = Task.query.filter_by(completada=True).count()
    tareas_vencidas = Task.query.filter(
        Task.completada == False,
        Task.fecha_vencimiento != None,
        Task.fecha_vencimiento < datetime.utcnow()
    ).count()
    
    # Actividades recientes
    actividades_recientes = Activity.query.options(joinedload(Activity.opportunity).joinedload(Opportunity.contact))\
        .order_by(desc(Activity.fecha))\
        .limit(20).all()
    
    # Representantes con más oportunidades
    representantes = db.session.query(
        Opportunity.representante,
        func.count(Opportunity.id).label('count'),
        func.sum(Opportunity.valor_estimado).label('valor_total')
    ).filter(
        Opportunity.representante.isnot(None),
        Opportunity.representante != ''
    ).group_by(Opportunity.representante).order_by(desc('count')).limit(10).all()
    
    return render_template('crm_dashboard.html',
                         total_oportunidades=total_oportunidades,
                         oportunidades_activas=oportunidades_activas,
                         oportunidades_cerradas=oportunidades_cerradas,
                         valor_total=valor_total,
                         valor_pipeline=valor_pipeline,
                         metricas_estado=metricas_estado,
                         top_oportunidades=top_oportunidades,
                         tareas_pendientes=tareas_pendientes,
                         tareas_completadas=tareas_completadas,
                         tareas_vencidas=tareas_vencidas,
                         actividades_recientes=actividades_recientes,
                         representantes=representantes,
                         estados=estados)

@crm_bp.route('/api/crm/metricas')
def api_metricas():
    estados = ['Nuevo', 'En seguimiento', 'Oportunidad', 'Cerrado']
    
    # Contar oportunidades por estado
    datos_estado = {}
    for estado in estados:
        count = Opportunity.query.filter_by(estado=estado).count()
        valor = db.session.query(func.sum(Opportunity.valor_estimado)).filter(Opportunity.estado == estado).scalar() or 0
        datos_estado[estado] = {'count': count, 'valor': float(valor)}
    
    # Tareas por prioridad
    prioridades = ['Alta', 'Media', 'Baja']
    tareas_prioridad = {}
    for prioridad in prioridades:
        count = Task.query.filter_by(prioridad=prioridad, completada=False).count()
        tareas_prioridad[prioridad] = count
    
    return jsonify({
        'estados': datos_estado,
        'tareas_prioridad': tareas_prioridad,
        'total_valor': float(db.session.query(func.sum(Opportunity.valor_estimado)).scalar() or 0)
    })

@crm_bp.route('/crm/guardar_estado_nota/<int:opp_id>', methods=['POST'])
def guardar_estado_nota(opp_id):
    nuevo_estado = request.form['estado']
    nota = request.form['nota']
    opp = Opportunity.query.get(opp_id)
    if opp:
        estado_cambiado = opp.estado != nuevo_estado
        opp.estado = nuevo_estado
        opp.nota = nota
        opp.ultima_actividad = datetime.utcnow()
        db.session.commit()
        # Registrar actividad
        actividad = Activity(
            opportunity_id=opp_id,
            tipo='nota_estado',
            descripcion=f"Nota y estado actualizados. Estado: {nuevo_estado}",
            usuario=request.form.get('usuario', 'Usuario'),
            detalles={'nota': nota, 'estado': nuevo_estado}
        )
        db.session.add(actividad)
        db.session.commit()
        flash('Nota y estado guardados correctamente', 'success')
    return redirect(url_for('crm_bp.crm_panel'))

@crm_bp.route('/crm/actualizar_oportunidad/<int:opp_id>', methods=['POST'])
def actualizar_oportunidad(opp_id):
    opp = Opportunity.query.get(opp_id)
    if opp:
        # Actualizar valores
        valor_estimado = request.form.get('valor_estimado')
        probabilidad = request.form.get('probabilidad')
        fecha_cierre_estimada = request.form.get('fecha_cierre_estimada')
        representante = request.form.get('representante')
        
        if valor_estimado:
            opp.valor_estimado = float(valor_estimado)
        if probabilidad:
            opp.probabilidad = int(probabilidad)
        if fecha_cierre_estimada:
            from datetime import datetime
            opp.fecha_cierre_estimada = datetime.strptime(fecha_cierre_estimada, '%Y-%m-%d').date()
        if representante:
            opp.representante = representante
            
        opp.ultima_actividad = datetime.utcnow()
        
        # Registrar actividad
        actividad = Activity(
            opportunity_id=opp_id,
            tipo='actualizacion',
            descripcion=f'Oportunidad actualizada - Valor: ${valor_estimado or "N/A"}, Probabilidad: {probabilidad or "N/A"}%',
            usuario=request.form.get('usuario', 'Usuario'),
            detalles={'valor_estimado': valor_estimado, 'probabilidad': probabilidad, 'representante': representante}
        )
        db.session.add(actividad)
        db.session.commit()
        flash('Oportunidad actualizada correctamente', 'success')
    
    return redirect(url_for('crm_bp.detalle_oportunidad', opp_id=opp_id))

# === SISTEMA DE TAREAS ASIGNADAS ===

@crm_bp.route('/mis-tareas')
def mis_tareas():
    """Panel de tareas asignadas al usuario actual"""
    # Por ahora simulamos un usuario, luego se integrará con autenticación
    usuario_actual = request.args.get('usuario', 'vendedor1')
    
    # Obtener el usuario, crearlo si no existe
    user = User.query.filter_by(username=usuario_actual).first()
    if not user:
        from werkzeug.security import generate_password_hash
        user = User(
            username=usuario_actual,
            email=f'{usuario_actual}@example.com',
            password_hash=generate_password_hash('password123'),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Usuario {usuario_actual} creado automáticamente', 'info')
    
    # Filtros
    estado_filter = request.args.get('estado', 'pendientes')  # pendientes, completadas, vencidas
    prioridad_filter = request.args.get('prioridad', '')
    
    # Query base
    query = Task.query.filter_by(asignado_a_id=user.id).options(
        joinedload(Task.opportunity).joinedload(Opportunity.contact)
    )
    
    # Aplicar filtros
    if estado_filter == 'pendientes':
        query = query.filter_by(completada=False)
    elif estado_filter == 'completadas':
        query = query.filter_by(completada=True)
    elif estado_filter == 'vencidas':
        query = query.filter(
            Task.completada == False,
            Task.fecha_vencimiento != None,
            Task.fecha_vencimiento < datetime.now()
        )
    
    if prioridad_filter:
        query = query.filter_by(prioridad=prioridad_filter)
    
    # Ordenar por fecha de vencimiento, poniendo las tareas sin fecha al final
    tareas = query.order_by(
        Task.fecha_vencimiento.is_(None),
        Task.fecha_vencimiento.asc()
    ).all()
    
    # Obtener todos los usuarios para selector
    usuarios = User.query.order_by(User.username).all()
      # Estadísticas del usuario
    estadisticas = {
        'total': Task.query.filter_by(asignado_a_id=user.id).count(),
        'pendientes': Task.query.filter_by(asignado_a_id=user.id, completada=False).count(),
        'completadas': Task.query.filter_by(asignado_a_id=user.id, completada=True).count(),
        'vencidas': Task.query.filter(
            Task.asignado_a_id == user.id,
            Task.completada == False,
            Task.fecha_vencimiento != None,
            Task.fecha_vencimiento < datetime.now()
        ).count()
    }
    
    return render_template('mis_tareas.html', 
                         tareas=tareas, 
                         usuario_actual=user,
                         usuarios=usuarios,
                         estadisticas=estadisticas,
                         estado_filter=estado_filter,
                         prioridad_filter=prioridad_filter)

@crm_bp.route('/completar-tarea/<int:tarea_id>', methods=['POST'])
def completar_tarea(tarea_id):
    """Marcar una tarea como completada"""
    tarea = Task.query.get_or_404(tarea_id)
    
    resultado = request.form.get('resultado', '').strip()
    usuario = request.form.get('usuario', 'Usuario')
    redirect_to = request.form.get('redirect_to', request.referrer or url_for('crm_bp.crm_panel'))
    
    tarea.completada = True
    tarea.fecha_completada = datetime.utcnow()
    tarea.resultado = resultado
    
    # Actualizar última actividad de la oportunidad
    if tarea.opportunity:
        tarea.opportunity.ultima_actividad = datetime.utcnow()
    
    # Registrar actividad
    actividad = Activity(
        opportunity_id=tarea.opportunity_id,
        tipo='tarea_completada',
        descripcion=f'Tarea completada: {tarea.descripcion}',
        usuario=usuario,
        detalles={'tarea_id': tarea_id, 'resultado': resultado}
    )
    db.session.add(actividad)
    db.session.commit()
    
    flash('Tarea completada correctamente', 'success')
    
    # Redireccionar al lugar apropiado
    if 'mis-tareas' in redirect_to:
        return redirect(url_for('crm_bp.mis_tareas', usuario=usuario))
    elif 'detalle' in redirect_to:
        return redirect(redirect_to)
    else:
        return redirect(url_for('crm_bp.crm_panel'))

@crm_bp.route('/api/usuarios')
def get_usuarios():
    """API para obtener lista de usuarios para asignación"""
    usuarios = User.query.order_by(User.username).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role
    } for u in usuarios])

@crm_bp.route('/asignar-tarea', methods=['POST'])
def asignar_tarea():
    """Asignar una tarea existente a un usuario"""
    tarea_id = request.form.get('tarea_id')
    usuario_id = request.form.get('usuario_id')
    
    if not tarea_id or not usuario_id:
        return jsonify({'success': False, 'message': 'Datos incompletos'})
    
    tarea = Task.query.get(tarea_id)
    usuario = User.query.get(usuario_id)
    
    if not tarea or not usuario:
        return jsonify({'success': False, 'message': 'Tarea o usuario no encontrado'})
    
    tarea.asignado_a_id = usuario_id
    
    # Registrar actividad
    actividad = Activity(
        opportunity_id=tarea.opportunity_id,
        tipo='tarea_asignada',
        descripcion=f'Tarea asignada a {usuario.username}: {tarea.descripcion}',
        usuario=request.form.get('asignado_por', 'Sistema')
    )
    db.session.add(actividad)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Tarea asignada a {usuario.username}'})

@crm_bp.route('/api/actividades/<int:opp_id>')
def get_actividades_ajax(opp_id):
    """API para cargar actividades de forma paginada"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    actividades = Activity.query.filter_by(opportunity_id=opp_id)\
        .order_by(desc(Activity.fecha))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    actividades_data = []
    for actividad in actividades.items:
        actividades_data.append({
            'id': actividad.id,
            'tipo': actividad.tipo,
            'descripcion': actividad.descripcion,
            'fecha': actividad.fecha.strftime('%d/%m/%Y %H:%M'),
            'usuario': actividad.usuario,
            'detalles': actividad.detalles
        })
    
    return jsonify({
        'actividades': actividades_data,
        'has_next': actividades.has_next,
        'has_prev': actividades.has_prev,
        'page': actividades.page,
        'pages': actividades.pages,
        'total': actividades.total
    })

@crm_bp.route('/api/tareas/<int:opp_id>')
def get_tareas_ajax(opp_id):
    """API para cargar todas las tareas de una oportunidad"""
    oportunidad = Opportunity.query.get_or_404(opp_id)
    
    tareas_data = []
    for tarea in oportunidad.tareas:
        tareas_data.append({
            'id': tarea.id,
            'descripcion': tarea.descripcion,
            'completada': tarea.completada,
            'prioridad': tarea.prioridad,
            'fecha_vencimiento': tarea.fecha_vencimiento.strftime('%d/%m/%Y') if tarea.fecha_vencimiento else None,
            'fecha_completada': tarea.fecha_completada.strftime('%d/%m/%Y %H:%M') if tarea.fecha_completada else None,
            'asignado_a': tarea.asignado_a.username if tarea.asignado_a else None,
            'resultado': tarea.resultado
        })
    
    return jsonify({
        'tareas': tareas_data,
        'total': len(tareas_data)
    })

# === FIN SISTEMA DE TAREAS ASIGNADAS ===
