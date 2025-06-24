class EmailProcessor {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.currentEmails = [];
    }

    initializeElements() {
        this.summarizeBtn = document.getElementById('summarizeBtn');
        this.status = document.getElementById('status');
        this.loading = document.getElementById('loading');
        this.emailsSection = document.getElementById('emailsSection');
        this.emailsList = document.getElementById('emailsList');
        this.emailCount = document.getElementById('emailCount');
        this.emailDetail = document.getElementById('emailDetail');
        this.emailDetailContent = document.getElementById('emailDetailContent');
        this.backBtn = document.getElementById('backBtn');
        this.filtersSection = document.getElementById('filtersSection');
        this.importanceFilter = document.getElementById('importanceFilter');
        this.deadlineFilter = document.getElementById('deadlineFilter');
        this.clearFiltersBtn = document.getElementById('clearFiltersBtn');
    }

    bindEvents() {
        this.summarizeBtn.addEventListener('click', () => this.processEmails());
        this.backBtn.addEventListener('click', () => this.showEmailsList());
        this.importanceFilter.addEventListener('change', () => this.applyFilters());
        this.deadlineFilter.addEventListener('change', () => this.applyFilters());
        this.clearFiltersBtn.addEventListener('click', () => this.clearFilters());
    }

    async processEmails() {
        this.showLoading(true);
        this.updateStatus('', '');
        this.summarizeBtn.disabled = true;

        try {
            const response = await fetch('/api/process-emails', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                this.currentEmails = data.emails;
                const methodBadge = data.method === 'LLM-powered' 
                    ? '<span class="method-badge llm-badge">🤖 LLM-Powered</span>' 
                    : '<span class="method-badge simple-badge">📝 Basic Processing</span>';
                this.updateStatus(`${data.message} ${methodBadge}`, 'success');
                this.displayEmails();
            } else {
                this.updateStatus(`Error: ${data.message}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`Network error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            this.summarizeBtn.disabled = false;
        }
    }

    displayEmails(emailsToShow = null) {
        const emails = emailsToShow || this.currentEmails;
        
        if (emails.length === 0) {
            this.emailCount.textContent = emailsToShow ? 'No emails match the current filters.' : 'No unread emails found.';
            this.emailsList.innerHTML = '<div class="no-emails">All caught up! No unread emails to process.</div>';
        } else {
            const filterText = emailsToShow && emailsToShow.length !== this.currentEmails.length 
                ? ` (${emails.length} of ${this.currentEmails.length} shown)`
                : '';
            this.emailCount.textContent = `Found ${emails.length} unread email${emails.length > 1 ? 's' : ''}${filterText}:`;
            this.emailsList.innerHTML = '';

            emails.forEach(email => {
                const emailItem = this.createEmailItem(email);
                this.emailsList.appendChild(emailItem);
            });
        }

        this.emailsSection.style.display = 'block';
        this.emailDetail.style.display = 'none';
        this.filtersSection.style.display = this.currentEmails.length > 0 ? 'block' : 'none';
    }

    createEmailItem(email) {
        const item = document.createElement('div');
        item.className = 'email-item';
        item.addEventListener('click', () => this.showEmailDetail(email.id));

        const badges = [];
        
        // Show importance level with appropriate color
        if (email.importance_level) {
            const importanceColors = {
                'Very Important': 'badge-very-important',
                'Important': 'badge-important',
                'Unimportant': 'badge-unimportant'
            };
            const colorClass = importanceColors[email.importance_level] || 'badge-unimportant';
            badges.push(`<span class="email-badge ${colorClass}">${email.importance_level}</span>`);
        }

        item.innerHTML = `
            <div class="email-subject">${this.escapeHtml(email.subject)}</div>
            <div class="email-sender">
                <i class="fas fa-user"></i> ${this.escapeHtml(email.from_name || email.from_email || 'Unknown Sender')}
            </div>
            <div class="email-meta">
                ${badges.join('')}
                <span class="email-date">
                    <i class="fas fa-envelope"></i> Click to view summary
                </span>
            </div>
        `;

        return item;
    }

    async showEmailDetail(emailId) {
        this.showLoading(true);

        try {
            const response = await fetch(`/api/email/${emailId}`);
            const data = await response.json();

            if (data.success) {
                this.displayEmailDetail(data.email);
                this.emailsSection.style.display = 'none';
                this.emailDetail.style.display = 'block';
            } else {
                this.updateStatus(`Error loading email: ${data.message}`, 'error');
            }
        } catch (error) {
            this.updateStatus(`Network error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayEmailDetail(email) {
        const importanceDisplay = email.importance_level 
            ? (() => {
                const importanceColors = {
                    'VERY_IMPORTANT': 'badge-very-important',
                    'IMPORTANT': 'badge-important', 
                    'UNIMPORTANT': 'badge-unimportant',
                    'SPAM': 'badge-spam'
                };
                const colorClass = importanceColors[email.importance_level] || 'badge-category';
                return `<span class="email-badge ${colorClass}">${email.importance_level.replace('_', ' ')}</span>`;
            })()
            : '<span class="text-muted">Not classified</span>';

        const deadlines = email.deadlines && email.deadlines.length > 0
            ? email.deadlines.map(deadline => {
                // Try to parse as date, if it fails, return the original string
                const date = new Date(deadline);
                if (isNaN(date.getTime())) {
                    // Not a valid date, return the original deadline text
                    return this.escapeHtml(deadline);
                } else {
                    // Valid date, format it nicely
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                }
              }).join(', ')
            : 'No deadlines found';

        // Format summary
        const summary = email.summary || 'No summary available';

        // Format important links
        const importantLinks = email.important_links && email.important_links.length > 0
            ? email.important_links.map(link => 
                `<div class="link-item">
                    <i class="fas fa-external-link-alt"></i>
                    <a href="${this.escapeHtml(link)}" target="_blank" rel="noopener noreferrer">
                        ${this.escapeHtml(link)}
                    </a>
                </div>`
              ).join('')
            : '<div class="text-muted">No important links found</div>';

        // Format attachments mentioned
        const attachmentsMentioned = email.attachments_mentioned && email.attachments_mentioned.length > 0
            ? email.attachments_mentioned.map(attachment => 
                `<div class="attachment-item">
                    <i class="fas fa-paperclip"></i>
                    ${this.escapeHtml(attachment)}
                </div>`
              ).join('')
            : '<div class="text-muted">No documents mentioned</div>';

        this.emailDetailContent.innerHTML = `
            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-user"></i> From
                </div>
                <div class="detail-value">
                    ${this.escapeHtml(email.from_name || email.from_email || 'Unknown Sender')}
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-envelope"></i> Subject
                </div>
                <div class="detail-value">
                    ${this.escapeHtml(email.subject)}
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-file-alt"></i> Summary
                </div>
                <div class="detail-value">
                    <div class="summary-text">
                        ${this.escapeHtml(summary)}
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-star"></i> Importance Level
                </div>
                <div class="detail-value">
                    <div class="importance-display">
                        ${importanceDisplay}
                    </div>
                </div>
            </div>

            ${email.deadlines && email.deadlines.length > 0 ? `
            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-calendar-alt"></i> Deadlines
                </div>
                <div class="detail-value">
                    <div class="deadlines-list">
                        ${deadlines}
                    </div>
                </div>
            </div>
            ` : ''}

            ${email.important_links && email.important_links.length > 0 ? `
            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-link"></i> Important Links
                </div>
                <div class="detail-value">
                    <div class="links-list">
                        ${importantLinks}
                    </div>
                </div>
            </div>
            ` : ''}

            ${email.attachments_mentioned && email.attachments_mentioned.length > 0 ? `
            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-paperclip"></i> Documents Mentioned
                </div>
                <div class="detail-value">
                    <div class="attachments-list">
                        ${attachmentsMentioned}
                    </div>
                </div>
            </div>
            ` : ''}

            <div class="detail-section">
                <div class="detail-label">
                    <i class="fas fa-info-circle"></i> Processing Info
                </div>
                <div class="detail-value">
                    <strong>Processed:</strong> ${email.processed_at}
                </div>
            </div>
        `;
    }

    showEmailsList() {
        this.emailsSection.style.display = 'block';
        this.emailDetail.style.display = 'none';
    }

    showLoading(show) {
        this.loading.style.display = show ? 'flex' : 'none';
    }

    updateStatus(message, type) {
        this.status.innerHTML = message;
        this.status.className = `status ${type}`;
        this.status.style.display = message ? 'block' : 'none';
    }

    applyFilters() {
        if (!this.currentEmails || this.currentEmails.length === 0) {
            return;
        }

        const importanceFilter = this.importanceFilter.value;
        const deadlineFilter = this.deadlineFilter.value;

        let filteredEmails = this.currentEmails;

        // Filter by importance
        if (importanceFilter !== 'ALL') {
            filteredEmails = filteredEmails.filter(email => 
                email.importance_level === importanceFilter
            );
        }

        // Filter by deadlines
        if (deadlineFilter === 'WITH_DEADLINES') {
            filteredEmails = filteredEmails.filter(email => 
                email.has_deadline || (email.deadlines && email.deadlines.length > 0)
            );
        } else if (deadlineFilter === 'NO_DEADLINES') {
            filteredEmails = filteredEmails.filter(email => 
                !email.has_deadline && (!email.deadlines || email.deadlines.length === 0)
            );
        }

        this.displayEmails(filteredEmails);
    }

    clearFilters() {
        this.importanceFilter.value = 'ALL';
        this.deadlineFilter.value = 'ALL';
        this.displayEmails();
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new EmailProcessor();
}); 