// Calendario Ticket - JavaScript con Drag & Drop

class TicketCalendar {
    constructor() {
        this.draggedTicket = null;
        this.draggedElement = null;
        this.viewMode = 'month'; // month, week, day
        this.currentDate = new Date();
        this.maxVisibleTickets = 2;
        this.init();
    }

    init() {
        // Salva l'HTML originale della vista mensile
        this.originalMonthHTML = document.querySelector('.calendar-grid').innerHTML;
        
        this.setupEventListeners();
        this.highlightToday();
        this.updateTodayIndicator();
        this.limitVisibleTickets();
        this.setupViewModeButtons();
    }

    setupEventListeners() {
        // Drag events per ticket nella sidebar
        const ticketItems = document.querySelectorAll('.ticket-item');
        ticketItems.forEach(item => {
            item.addEventListener('dragstart', this.onTicketDragStart.bind(this));
            item.addEventListener('dragend', this.onTicketDragEnd.bind(this));
        });

        // Drop events per giorni del calendario
        const calendarDays = document.querySelectorAll('.calendar-day:not(.empty)');
        calendarDays.forEach(day => {
            day.addEventListener('dragover', this.onCalendarDragOver.bind(this));
            day.addEventListener('dragenter', this.onCalendarDragEnter.bind(this));
            day.addEventListener('dragleave', this.onCalendarDragLeave.bind(this));
            day.addEventListener('drop', this.onCalendarDrop.bind(this));
            day.addEventListener('click', this.onDayClick.bind(this));
        });

        // Click events per ticket nel calendario
        const calendarTickets = document.querySelectorAll('.calendar-ticket');
        calendarTickets.forEach(ticket => {
            ticket.addEventListener('click', this.onCalendarTicketClick.bind(this));
            ticket.addEventListener('dragstart', this.onCalendarTicketDragStart.bind(this));
            ticket.addEventListener('dragend', this.onTicketDragEnd.bind(this));
        });

        // Aggiungi drag capability ai ticket nel calendario
        calendarTickets.forEach(ticket => {
            ticket.draggable = true;
        });

        // Drop zone per rimuovere ticket (sidebar)
        const ticketList = document.querySelector('.ticket-list');
        if (ticketList) {
            ticketList.addEventListener('dragover', this.onSidebarDragOver.bind(this));
            ticketList.addEventListener('drop', this.onSidebarDrop.bind(this));
        }

        // Click su overflow tickets
        const overflowIndicators = document.querySelectorAll('.tickets-overflow');
        overflowIndicators.forEach(indicator => {
            indicator.addEventListener('click', this.onOverflowClick.bind(this));
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', this.onKeyDown.bind(this));
    }

    limitVisibleTickets() {
        const dayTicketsContainers = document.querySelectorAll('.day-tickets');
        
        dayTicketsContainers.forEach(container => {
            const tickets = container.querySelectorAll('.calendar-ticket');
            
            if (tickets.length > this.maxVisibleTickets) {
                // Nascondi i ticket dal terzo in poi
                for (let i = this.maxVisibleTickets; i < tickets.length; i++) {
                    tickets[i].style.display = 'none';
                }
                
                // Aggiungi indicatore overflow se non esiste già
                if (!container.querySelector('.tickets-overflow')) {
                    const overflowCount = tickets.length - this.maxVisibleTickets;
                    const overflowIndicator = document.createElement('div');
                    overflowIndicator.className = 'tickets-overflow';
                    overflowIndicator.textContent = `+${overflowCount} altri`;
                    overflowIndicator.dataset.totalTickets = tickets.length;
                    container.appendChild(overflowIndicator);
                }
            }
        });
    }

    setupViewModeButtons() {
        // Questa funzione verrà chiamata quando i pulsanti sono presenti nel template
        const viewButtons = document.querySelectorAll('.view-mode-btn');
        viewButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const mode = e.target.dataset.mode;
                await this.switchViewMode(mode);
            });
        });
    }

    async switchViewMode(mode) {
        this.viewMode = mode;
        
        // Aggiorna i pulsanti attivi
        document.querySelectorAll('.view-mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        
        // Aggiorna la vista
        await this.updateCalendarView();
    }

    async updateCalendarView() {
        const calendarContainer = document.querySelector('.calendar-container');
        const calendarGrid = document.querySelector('.calendar-grid');
        
        // Rimuovi classi di visualizzazione esistenti
        calendarContainer.classList.remove('month-view', 'week-view', 'day-view');
        
        // Applica la nuova vista
        switch(this.viewMode) {
            case 'day':
                await this.renderDayView();
                break;
            case 'week':
                await this.renderWeekView();
                break;
            case 'month':
            default:
                this.renderMonthView();
                break;
        }
    }

    renderMonthView() {
        const calendarContainer = document.querySelector('.calendar-container');
        calendarContainer.classList.add('month-view');
        
        // Se siamo in una vista diversa, ricarica la pagina per ripristinare la vista mensile originale
        if (this.viewMode !== 'month' && this.originalMonthHTML) {
            console.log('Switching back to month view - reloading page');
            window.location.reload();
            return;
        }
        
        console.log('Month view activated');
    }



    async renderWeekView() {
        const calendarContainer = document.querySelector('.calendar-container');
        const calendarGrid = document.querySelector('.calendar-grid');
        calendarContainer.classList.add('week-view');
        
        // Calcola la settimana corrente
        const today = new Date();
        const currentWeek = this.getCurrentWeek(today);
        
        // Carica i ticket per la settimana
        const weekTickets = await this.loadWeekTickets(currentWeek);
        
        // Crea la vista settimanale
        let weekHtml = `
            <div class="week-header">
                <div class="week-time-header"></div>
                ${currentWeek.map(day => `
                    <div class="week-day-header">
                        <div class="week-day-name">${day.toLocaleDateString('it-IT', { weekday: 'short' })}</div>
                        <div class="week-day-number">${day.getDate()}</div>
                    </div>
                `).join('')}
            </div>
            <div class="week-body">
                ${this.generateWeekTimeSlots(currentWeek, weekTickets)}
            </div>
        `;
        
        calendarGrid.innerHTML = weekHtml;
        
        // Reinizializza gli event listeners per la vista settimanale
        this.setupWeekViewListeners();
        console.log('Week view activated');
    }

    async renderDayView() {
        const calendarContainer = document.querySelector('.calendar-container');
        const calendarGrid = document.querySelector('.calendar-grid');
        calendarContainer.classList.add('day-view');
        
        const today = new Date();
        
        // Carica i ticket per il giorno
        const dayTickets = await this.loadDayTickets(today);
        
        // Crea la vista giornaliera
        let dayHtml = `
            <div class="day-view-header">
                <h3>${today.toLocaleDateString('it-IT', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                })}</h3>
            </div>
            <div class="day-view-content">
                <div class="day-time-slots">
                    ${this.generateDayTimeSlots()}
                </div>
                <div class="day-events-container">
                    ${this.generateDayEvents(today, dayTickets)}
                </div>
            </div>
        `;
        
        calendarGrid.innerHTML = dayHtml;
        
        // Reinizializza gli event listeners per la vista giornaliera
        this.setupDayViewListeners();
        console.log('Day view activated');
    }

    getCurrentWeek(date) {
        const week = [];
        const startOfWeek = new Date(date);
        const day = startOfWeek.getDay();
        const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // Lunedì come primo giorno
        startOfWeek.setDate(diff);
        
        for (let i = 0; i < 7; i++) {
            const weekDay = new Date(startOfWeek);
            weekDay.setDate(startOfWeek.getDate() + i);
            week.push(weekDay);
        }
        
        return week;
    }

    generateWeekTimeSlots(weekDays, weekTickets = {}) {
        let slotsHtml = '';
        
        for (let hour = 8; hour < 20; hour++) {
            slotsHtml += `
                <div class="week-time-row">
                    <div class="week-time-slot">${hour}:00</div>
                    ${weekDays.map(day => {
                        const dateStr = this.formatDate(day);
                        const dayTickets = weekTickets[dateStr] || [];
                        
                        // Mostra i ticket solo nella prima riga (8:00) per ogni giorno
                        const ticketsHtml = hour === 8 && dayTickets.length > 0 ? 
                            dayTickets.slice(0, 3).map((ticket, index) => `
                                <div class="week-ticket priority-${ticket.priorita.toLowerCase()}" 
                                     data-ticket-id="${ticket.id}"
                                     title="${ticket.numero_ticket}: ${ticket.titolo}"
                                     style="top: ${5 + (index * 25)}px;">
                                    <div class="ticket-number">${ticket.numero_ticket}</div>
                                    <div class="ticket-title-short">${ticket.titolo.substring(0, 15)}${ticket.titolo.length > 15 ? '...' : ''}</div>
                                </div>
                            `).join('') : '';
                        
                        const overflowHtml = hour === 8 && dayTickets.length > 3 ? 
                            `<div class="week-overflow">+${dayTickets.length - 3}</div>` : '';
                        
                        return `
                            <div class="week-day-column" 
                                 data-date="${dateStr}" 
                                 data-hour="${hour}">
                                ${ticketsHtml}
                                ${overflowHtml}
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }
        
        return slotsHtml;
    }

    generateDayTimeSlots() {
        let slotsHtml = '';
        
        for (let hour = 8; hour < 20; hour++) {
            slotsHtml += `
                <div class="day-time-slot">${hour}:00</div>
            `;
        }
        
        return slotsHtml;
    }

    generateDayEvents(date, dayTickets = []) {
        let eventsHtml = '';
        
        // Distribuisci i ticket nelle prime 3 ore della giornata (8:00, 9:00, 10:00)
        const ticketsPerHour = Math.ceil(dayTickets.length / 3);
        
        for (let hour = 8; hour < 20; hour++) {
            let hourTickets = [];
            
            // Distribuisci i ticket solo nelle prime ore
            if (hour >= 8 && hour <= 10 && dayTickets.length > 0) {
                const startIndex = (hour - 8) * ticketsPerHour;
                const endIndex = Math.min(startIndex + ticketsPerHour, dayTickets.length);
                hourTickets = dayTickets.slice(startIndex, endIndex);
            }
            
            const ticketsHtml = hourTickets.map((ticket, index) => `
                <div class="day-ticket priority-${ticket.priorita.toLowerCase()}" 
                     data-ticket-id="${ticket.id}"
                     title="${ticket.numero_ticket}: ${ticket.titolo}"
                     style="top: ${5 + (index * 60)}px; z-index: ${10 + index};">
                    <div class="ticket-number">${ticket.numero_ticket}</div>
                    <div class="ticket-title">${ticket.titolo}</div>
                    <div class="ticket-client">${ticket.cliente}</div>
                </div>
            `).join('');
            
            eventsHtml += `
                <div class="day-hour-line" 
                     data-date="${this.formatDate(date)}" 
                     data-hour="${hour}">
                    ${ticketsHtml}
                </div>
            `;
        }
        
        return eventsHtml;
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    async loadWeekTickets(weekDays) {
        const weekTickets = {};
        
        try {
            // Carica i ticket per ogni giorno della settimana
            for (const day of weekDays) {
                const dateStr = this.formatDate(day);
                const response = await fetch(`/tickets/api/calendar-tickets?date=${dateStr}`);
                const data = await response.json();
                
                if (data.tickets && data.tickets.length > 0) {
                    weekTickets[dateStr] = data.tickets;
                }
            }
        } catch (error) {
            console.error('Error loading week tickets:', error);
        }
        
        return weekTickets;
    }

    async loadDayTickets(date) {
        try {
            const dateStr = this.formatDate(date);
            const response = await fetch(`/tickets/api/calendar-tickets?date=${dateStr}`);
            const data = await response.json();
            
            return data.tickets || [];
        } catch (error) {
            console.error('Error loading day tickets:', error);
            return [];
        }
    }

    setupWeekViewListeners() {
        // Aggiungi eventi per il drop nelle colonne settimanali
        const weekColumns = document.querySelectorAll('.week-day-column');
        weekColumns.forEach(column => {
            column.addEventListener('dragover', this.onCalendarDragOver.bind(this));
            column.addEventListener('dragenter', this.onCalendarDragEnter.bind(this));
            column.addEventListener('dragleave', this.onCalendarDragLeave.bind(this));
            column.addEventListener('drop', this.onWeekDrop.bind(this));
        });

        // Aggiungi eventi per i ticket nella vista settimanale
        const weekTickets = document.querySelectorAll('.week-ticket');
        weekTickets.forEach(ticket => {
            ticket.addEventListener('click', this.onCalendarTicketClick.bind(this));
            ticket.addEventListener('dragstart', this.onCalendarTicketDragStart.bind(this));
            ticket.addEventListener('dragend', this.onTicketDragEnd.bind(this));
            ticket.draggable = true;
        });

        // Aggiungi eventi per l'overflow nella vista settimanale
        const weekOverflows = document.querySelectorAll('.week-overflow');
        weekOverflows.forEach(overflow => {
            overflow.addEventListener('click', this.onWeekOverflowClick.bind(this));
        });
    }

    setupDayViewListeners() {
        // Aggiungi eventi per il drop nelle ore giornaliere
        const dayLines = document.querySelectorAll('.day-hour-line');
        dayLines.forEach(line => {
            line.addEventListener('dragover', this.onCalendarDragOver.bind(this));
            line.addEventListener('dragenter', this.onCalendarDragEnter.bind(this));
            line.addEventListener('dragleave', this.onCalendarDragLeave.bind(this));
            line.addEventListener('drop', this.onDayDrop.bind(this));
        });

        // Aggiungi eventi per i ticket nella vista giornaliera
        const dayTickets = document.querySelectorAll('.day-ticket');
        dayTickets.forEach(ticket => {
            ticket.addEventListener('click', this.onCalendarTicketClick.bind(this));
            ticket.addEventListener('dragstart', this.onCalendarTicketDragStart.bind(this));
            ticket.addEventListener('dragend', this.onTicketDragEnd.bind(this));
            ticket.draggable = true;
        });
    }

    onWeekDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        const column = e.target.closest('.week-day-column');
        column.classList.remove('drag-over');
        
        if (!this.draggedTicket) return;

        const date = column.dataset.date;
        if (!date) return;

        this.updateTicketDate(this.draggedTicket.id, date);
    }

    onDayDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        const line = e.target.closest('.day-hour-line');
        line.classList.remove('drag-over');
        
        if (!this.draggedTicket) return;

        const date = line.dataset.date;
        if (!date) return;

        this.updateTicketDate(this.draggedTicket.id, date);
    }

    onTicketDragStart(e) {
        this.draggedTicket = {
            id: e.target.dataset.ticketId,
            number: e.target.dataset.ticketNumber,
            title: e.target.dataset.ticketTitle,
            priority: e.target.dataset.ticketPriority,
            status: e.target.dataset.ticketStatus,
            element: e.target
        };
        
        this.draggedElement = e.target;
        e.target.classList.add('dragging');
        
        // Set drag effect
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);
        
        // Create custom drag image
        const dragImage = this.createDragImage(e.target);
        document.body.appendChild(dragImage);
        e.dataTransfer.setDragImage(dragImage, 50, 25);
        
        // Remove drag image after drag starts
        setTimeout(() => {
            if (dragImage.parentNode) {
                dragImage.parentNode.removeChild(dragImage);
            }
        }, 0);

        this.showDropZones();
    }

    onCalendarTicketDragStart(e) {
        e.stopPropagation(); // Previene il click sul giorno
        
        // Drag ticket dal calendario per rimuoverlo o spostarlo
        this.draggedTicket = {
            id: e.target.dataset.ticketId,
            element: e.target,
            fromCalendar: true
        };
        
        this.draggedElement = e.target;
        e.target.classList.add('dragging');
        
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);

        this.showDropZones();
    }

    onTicketDragEnd(e) {
        e.target.classList.remove('dragging');
        this.hideDropZones();
        this.draggedTicket = null;
        this.draggedElement = null;
    }

    onCalendarDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    onCalendarDragEnter(e) {
        e.preventDefault();
        e.target.closest('.calendar-day').classList.add('drag-over');
    }

    onCalendarDragLeave(e) {
        // Check if we're actually leaving the day (not just entering a child)
        const day = e.target.closest('.calendar-day');
        if (day && !day.contains(e.relatedTarget)) {
            day.classList.remove('drag-over');
        }
    }

    onCalendarDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        const day = e.target.closest('.calendar-day');
        day.classList.remove('drag-over');

        if (!this.draggedTicket) {
            console.warn('No dragged ticket found');
            return;
        }

        const date = day.dataset.date;
        if (!date) {
            console.warn('No date found in day dataset');
            return;
        }

        console.log('Dropping ticket on date:', date);
        this.updateTicketDate(this.draggedTicket.id, date);
    }

    onSidebarDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    onSidebarDrop(e) {
        e.preventDefault();
        
        if (!this.draggedTicket || !this.draggedTicket.fromCalendar) return;
        
        // Remove ticket from calendar (set date to null)
        this.updateTicketDate(this.draggedTicket.id, null);
    }

    onDayClick(e) {
        // Evita il trigger se si sta facendo drag o click su ticket
        if (e.target.closest('.calendar-ticket') || this.draggedTicket) return;
        
        const day = e.target.closest('.calendar-day');
        if (!day || day.classList.contains('empty')) return;
        
        const date = day.dataset.date;
        if (date) {
            this.showDayModal(date);
        }
    }

    onOverflowClick(e) {
        e.stopPropagation();
        const container = e.target.closest('.day-tickets');
        const day = container.closest('.calendar-day');
        const date = day.dataset.date;
        
        if (date) {
            this.showDayModal(date);
        }
    }

    onWeekOverflowClick(e) {
        e.stopPropagation();
        const column = e.target.closest('.week-day-column');
        const date = column.dataset.date;
        
        if (date) {
            this.showDayModal(date);
        }
    }

    async showDayModal(date) {
        try {
            const response = await fetch(`/tickets/api/calendar-tickets?date=${date}`);
            const data = await response.json();
            
            if (data.tickets) {
                this.renderDayModal(date, data.tickets);
            }
        } catch (error) {
            console.error('Error loading day tickets:', error);
            this.showNotification('Errore nel caricamento dei ticket del giorno', 'error');
        }
    }

    renderDayModal(date, tickets) {
        const modal = document.getElementById('dayModal') || this.createDayModal();
        const modalTitle = modal.querySelector('.modal-title');
        const modalBody = modal.querySelector('.modal-body');
        
        // Format date
        const dateObj = new Date(date + 'T00:00:00');
        const formattedDate = dateObj.toLocaleDateString('it-IT', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        modalTitle.innerHTML = `<i class="bi bi-calendar-day"></i> ${formattedDate}`;
        
        if (tickets.length === 0) {
            modalBody.innerHTML = `
                <div class="text-center p-4 text-muted">
                    <i class="bi bi-calendar-x fs-1"></i>
                    <p class="mt-2">Nessun ticket programmato per questo giorno</p>
                </div>
            `;
        } else {
            let ticketsHtml = '<div class="day-modal-tickets">';
            
            tickets.forEach(ticket => {
                ticketsHtml += `
                    <div class="day-modal-ticket priority-${ticket.priorita.toLowerCase()}" 
                         onclick="window.location.href='/tickets/${ticket.id}'">
                        <div class="ticket-header-modal">
                            <div class="ticket-number-modal">${ticket.numero_ticket}</div>
                            <div class="priority-badge priority-${ticket.priorita.toLowerCase()}">
                                ${ticket.priorita}
                            </div>
                        </div>
                        <div class="ticket-title-modal">${ticket.titolo}</div>
                        <div class="ticket-info-modal">
                            <small class="text-muted">
                                <i class="bi bi-building"></i> ${ticket.cliente}
                                ${ticket.assigned_to ? `<br><i class="bi bi-person"></i> ${ticket.assigned_to}` : ''}
                            </small>
                        </div>
                        <div class="ticket-status-modal">
                            <span class="badge status-${ticket.stato.toLowerCase().replace(' ', '-')}">
                                ${ticket.stato}
                            </span>
                        </div>
                    </div>
                `;
            });
            
            ticketsHtml += '</div>';
            modalBody.innerHTML = ticketsHtml;
        }
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    createDayModal() {
        const modalHtml = `
            <div class="modal fade" id="dayModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"></h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body"></div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add CSS for day modal tickets
        const style = document.createElement('style');
        style.textContent = `
            .day-modal-tickets {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            
            .day-modal-ticket {
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid;
                cursor: pointer;
                transition: all 0.2s ease;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .day-modal-ticket:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .day-modal-ticket.priority-critica {
                border-left-color: #ef4444;
                background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            }
            
            .day-modal-ticket.priority-alta {
                border-left-color: #f59e0b;
                background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
            }
            
            .day-modal-ticket.priority-media {
                border-left-color: #06b6d4;
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            }
            
            .day-modal-ticket.priority-bassa {
                border-left-color: #10b981;
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            }
            
            .ticket-header-modal {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5rem;
            }
            
            .ticket-number-modal {
                font-weight: 600;
                color: var(--primary-color);
                font-size: 0.9rem;
            }
            
            .ticket-title-modal {
                font-weight: 500;
                margin-bottom: 0.5rem;
                color: #1e293b;
            }
            
            .ticket-info-modal {
                margin-bottom: 0.5rem;
            }
            
            .ticket-status-modal {
                display: flex;
                justify-content: flex-end;
            }
        `;
        document.head.appendChild(style);
        
        return document.getElementById('dayModal');
    }

    createDragImage(element) {
        const dragImage = element.cloneNode(true);
        dragImage.style.position = 'absolute';
        dragImage.style.top = '-1000px';
        dragImage.style.left = '-1000px';
        dragImage.style.width = element.offsetWidth + 'px';
        dragImage.style.opacity = '0.8';
        dragImage.style.transform = 'rotate(5deg)';
        dragImage.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
        dragImage.style.zIndex = '9999';
        return dragImage;
    }

    showDropZones() {
        // Show drop zones based on current view
        if (this.viewMode === 'month') {
            document.querySelectorAll('.calendar-day:not(.empty)').forEach(day => {
                day.classList.add('drop-zone-active');
            });
        } else if (this.viewMode === 'week') {
            document.querySelectorAll('.week-day-column').forEach(column => {
                column.classList.add('drop-zone-active');
            });
        } else if (this.viewMode === 'day') {
            document.querySelectorAll('.day-hour-line').forEach(line => {
                line.classList.add('drop-zone-active');
            });
        }
        
        // Show sidebar as drop zone if dragging from calendar
        if (this.draggedTicket && this.draggedTicket.fromCalendar) {
            document.querySelector('.ticket-list').classList.add('drop-zone-active');
        }
    }

    hideDropZones() {
        document.querySelectorAll('.drop-zone-active').forEach(zone => {
            zone.classList.remove('drop-zone-active');
        });
    }

    async updateTicketDate(ticketId, date) {
        try {
            // Debug: log dei valori ricevuti
            console.log('updateTicketDate called with:', { ticketId, date });
            console.log('ticketId type:', typeof ticketId, 'value:', ticketId);

            // Validazione parametri
            if (!ticketId) {
                throw new Error(`Parametri mancanti: ticketId=${ticketId}, date=${date}`);
            }

            // Date può essere null per rimuovere dal calendario
            if (date !== null && date !== undefined && date !== '') {
                // Validazione formato data se presente
                if (typeof date !== 'string') {
                    throw new Error(`Date deve essere una stringa o null: ${date}`);
                }
            }

            // Assicurati che ticketId sia un numero
            const numericTicketId = parseInt(ticketId);
            if (isNaN(numericTicketId)) {
                throw new Error(`ticketId non è un numero valido: ${ticketId}`);
            }

            const response = await fetch('/tickets/api/update-ticket-date', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    ticket_id: numericTicketId,
                    date: date
                })
            });

            // Debug: log della risposta
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                
                // Reload page to update UI
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showNotification(result.message || 'Errore durante l\'aggiornamento', 'error');
            }
        } catch (error) {
            console.error('Error updating ticket date:', error);

            // Log dettagliato dell'errore
            if (error.message && error.message.includes('Unexpected token')) {
                console.error('Received HTML instead of JSON - likely a server error');
                this.showNotification('Errore del server: controlla la console per dettagli', 'error');
            } else {
                this.showNotification('Errore di connessione', 'error');
            }
        }
    }

    onCalendarTicketClick(e) {
        e.stopPropagation();
        const ticketId = e.target.closest('.calendar-ticket').dataset.ticketId;
        this.showTicketDetails(ticketId);
    }

    async showTicketDetails(ticketId) {
        try {
            // Redirect to ticket detail page
            window.location.href = `/tickets/${ticketId}`;
        } catch (error) {
            console.error('Error showing ticket details:', error);
            this.showNotification('Errore nel caricamento dettagli ticket', 'error');
        }
    }

    showNotification(message, type = 'success') {
        const toast = document.getElementById('notification-toast');
        const toastMessage = document.getElementById('toast-message');
        const toastHeader = toast.querySelector('.toast-header');
        
        // Update message
        toastMessage.textContent = message;
        
        // Update icon and style based on type
        const icon = toastHeader.querySelector('i');
        toast.classList.remove('toast-success', 'toast-error');
        
        if (type === 'success') {
            icon.className = 'bi bi-check-circle-fill text-success me-2';
            toast.classList.add('toast-success');
        } else {
            icon.className = 'bi bi-exclamation-circle-fill text-danger me-2';
            toast.classList.add('toast-error');
        }
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    highlightToday() {
        const today = new Date();
        const todayString = today.getFullYear() + '-' + 
                           String(today.getMonth() + 1).padStart(2, '0') + '-' + 
                           String(today.getDate()).padStart(2, '0');
        
        const todayElement = document.querySelector(`[data-date="${todayString}"]`);
        if (todayElement) {
            todayElement.classList.add('today');
        }
    }

    updateTodayIndicator() {
        // Update navigation based on current view mode
        const today = new Date();
        const isCurrentMonth = window.calendarData && 
                               window.calendarData.currentYear === today.getFullYear() && 
                               window.calendarData.currentMonth === today.getMonth() + 1;
        
        // This will be updated when we implement different view modes
    }

    onKeyDown(e) {
        // Keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigatePrevious();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateNext();
                    break;
                case 'Home':
                    e.preventDefault();
                    goToToday();
                    break;
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
    }

    navigatePrevious() {
        // Will be implemented based on view mode
        navigateMonth(-1);
    }

    navigateNext() {
        // Will be implemented based on view mode
        navigateMonth(1);
    }

    // Utility methods
    static formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    static parseDate(dateString) {
        return new Date(dateString + 'T00:00:00');
    }
}

// Initialize calendar when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.ticketCalendar = new TicketCalendar();
    
    // Add touch support for mobile devices
    if ('ontouchstart' in window) {
        addTouchSupport();
    }
});

// Touch support for mobile drag and drop
function addTouchSupport() {
    let touchItem = null;
    let touchOffset = { x: 0, y: 0 };
    
    document.addEventListener('touchstart', function(e) {
        const target = e.target.closest('.ticket-item, .calendar-ticket');
        if (target) {
            touchItem = target;
            const touch = e.touches[0];
            const rect = target.getBoundingClientRect();
            touchOffset.x = touch.clientX - rect.left;
            touchOffset.y = touch.clientY - rect.top;
            
            target.classList.add('dragging');
            e.preventDefault();
        }
    });
    
    document.addEventListener('touchmove', function(e) {
        if (touchItem) {
            e.preventDefault();
            const touch = e.touches[0];
            
            // Create visual feedback
            touchItem.style.position = 'fixed';
            touchItem.style.left = (touch.clientX - touchOffset.x) + 'px';
            touchItem.style.top = (touch.clientY - touchOffset.y) + 'px';
            touchItem.style.zIndex = '9999';
            touchItem.style.transform = 'rotate(5deg) scale(1.05)';
            
            // Highlight drop zones
            const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
            const dropZone = elementBelow?.closest('.calendar-day:not(.empty)');
            
            document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
            if (dropZone) {
                dropZone.classList.add('drag-over');
            }
        }
    });
    
    document.addEventListener('touchend', function(e) {
        if (touchItem) {
            const touch = e.changedTouches[0];
            const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
            const dropZone = elementBelow?.closest('.calendar-day:not(.empty)');
            
            // Reset styles
            touchItem.style.position = '';
            touchItem.style.left = '';
            touchItem.style.top = '';
            touchItem.style.zIndex = '';
            touchItem.style.transform = '';
            touchItem.classList.remove('dragging');
            
            document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
            
            // Handle drop
            if (dropZone && window.ticketCalendar) {
                const ticketId = touchItem.dataset.ticketId;
                const date = dropZone.dataset.date;
                if (ticketId && date) {
                    window.ticketCalendar.updateTicketDate(ticketId, date);
                }
            }
            
            touchItem = null;
        }
    });
}

// Global helper functions - Updated for view modes
window.navigateMonth = function(direction) {
    // This will be updated to handle different view modes
    let year, month;
    if (direction === 1) {
        year = window.calendarData.nextYear;
        month = window.calendarData.nextMonth;
    } else {
        year = window.calendarData.prevYear;
        month = window.calendarData.prevMonth;
    }
    window.location.href = `/tickets/calendar?year=${year}&month=${month}`;
};

window.goToToday = function() {
    const today = new Date();
    window.location.href = `/tickets/calendar?year=${today.getFullYear()}&month=${today.getMonth() + 1}`;
};

window.switchView = function(mode) {
    if (window.ticketCalendar) {
        window.ticketCalendar.switchViewMode(mode);
    }
};