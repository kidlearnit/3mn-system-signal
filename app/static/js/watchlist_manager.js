/**
 * Watchlist Manager - Handles watchlist operations
 */
class WatchlistManager {
    constructor() {
        this.baseUrl = '/api/v1/symbols';
    }
    
    loadWatchlist() {
        const watchlistContainer = document.getElementById('watchlist');
        const watchlistItems = document.getElementById('watchlistItems');
        
        // Check if add symbol form already exists and remove it
        const existingForm = document.getElementById('add-symbol-form');
        if (existingForm) {
            existingForm.remove();
        }
        
        // Create the add symbol form at the top
        this.createAddSymbolForm(watchlistContainer, watchlistItems);
        
        // Show loading state in the watchlist items
        watchlistItems.innerHTML = `
            <div class="flex justify-center items-center p-8">
                <span class="loading loading-spinner loading-md text-primary"></span>
                <span class="ml-2">Loading quotes...</span>
            </div>
        `;
        
        fetch(this.baseUrl)
            .then(response => response.json())
            .then(response => {
                // Extract items from API response
                const symbolsData = response.data && response.data.items ? response.data.items : [];
                this.renderWatchlistItems(watchlistItems, symbolsData);
            })
            .catch(error => {
                console.error('Error loading watchlist:', error);
                this.showWatchlistError(watchlistItems);
            });
    }
    
    createAddSymbolForm(watchlistContainer, watchlistItems) {
        const addForm = document.createElement('div');
        addForm.id = 'add-symbol-form';
        addForm.className = 'form-control mb-4 p-4 border-b border-base-300';
        addForm.innerHTML = `
            <div class="input-group">
                <input type="text" id="newSymbol" placeholder="Add new symbol..." 
                    class="input input-bordered w-full focus:outline-primary" />
                <button id="addSymbolBtn" class="btn btn-primary">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
            <div id="symbolError" class="text-error text-xs mt-1 hidden"></div>
        `;
        
        // Insert form before the watchlist items
        watchlistContainer.insertBefore(addForm, watchlistItems);
        
        // Add event listeners to the form
        document.getElementById('addSymbolBtn').addEventListener('click', () => this.addSymbol());
        document.getElementById('newSymbol').addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                this.addSymbol();
            }
        });
    }
    
    renderWatchlistItems(watchlistItems, symbolsData) {
        watchlistItems.innerHTML = '';
        
        if (symbolsData.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'flex flex-col items-center justify-center p-6 text-center text-opacity-70';
            emptyState.innerHTML = `
                <i class="fas fa-list text-3xl mb-2 text-primary opacity-50"></i>
                <p>No symbols in watchlist</p>
                <button class="btn btn-sm btn-outline btn-primary mt-2">Add Symbol</button>
            `;
            watchlistItems.appendChild(emptyState);
            return;
        }
        
        symbolsData.forEach(symbolData => {
            const item = this.createWatchlistItem(symbolData);
            watchlistItems.appendChild(item);
        });
        
        // Add refresh button
        this.addRefreshButton(watchlistItems);
    }
    
    createWatchlistItem(symbolData) {
        const item = document.createElement('div');
        item.className = 'card bg-base-100 hover:bg-base-200 shadow-sm hover:shadow cursor-pointer transition-all group relative';
        
        // Format the data
        const price = symbolData.price ? symbolData.price.toFixed(2) : 'N/A';
        const changePercent = symbolData.change ? symbolData.change.toFixed(2) : 0;
        const isPositive = changePercent > 0;
        const changeClass = isPositive ? 'text-success' : (changePercent < 0 ? 'text-error' : 'text-gray-500');
        const changeIcon = isPositive ? 'caret-up' : (changePercent < 0 ? 'caret-down' : 'minus');
        
        // Create tooltip with more info
        const tooltipContent = `${symbolData.name || symbolData.symbol}`;
        
        item.innerHTML = `
            <div class="card-body p-3" data-tip="${tooltipContent}">
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="font-bold">${symbolData.symbol}</h3>
                        <div class="text-xs opacity-70 truncate max-w-32" title="${symbolData.name || symbolData.symbol}">
                            ${symbolData.name || 'Yahoo Finance'}
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="font-medium">${price}</div>
                        <div class="text-xs ${changeClass}">
                            <i class="fas fa-${changeIcon} mr-1"></i>
                            ${changePercent}%
                        </div>
                    </div>
                </div>
                <button class="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:text-error delete-symbol" data-id="${symbolData.id}">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        `;
        
        // Add click event to load symbol data
        item.addEventListener('click', () => {
            document.getElementById('ticker').value = symbolData.symbol;
            // Add active indicator
            document.querySelectorAll('.card.border-primary').forEach(el => {
                el.classList.remove('border-primary', 'border');
            });
            item.classList.add('border-primary', 'border');
            
            // Trigger data fetch
            window.dispatchEvent(new CustomEvent('symbolSelected', { 
                detail: { 
                    symbol: symbolData.symbol,
                    emaPeriod: document.getElementById('emaPeriod').value,
                    rsiPeriod: document.getElementById('rsiPeriod').value
                } 
            }));
        });
        
        // Add delete event
        const deleteBtn = item.querySelector('.delete-symbol');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const symbolId = deleteBtn.getAttribute('data-id');
            if (confirm('Remove this symbol from watchlist?')) {
                this.removeSymbol(symbolId, item);
            }
        });
        
        return item;
    }
    
    addRefreshButton(watchlistItems) {
        const refreshButton = document.createElement('button');
        refreshButton.className = 'btn btn-sm btn-ghost gap-2 mt-4 w-full';
        refreshButton.innerHTML = `<i class="fas fa-sync-alt"></i> Refresh Quotes`;
        refreshButton.addEventListener('click', () => this.loadWatchlist());
        watchlistItems.appendChild(refreshButton);
    }
    
    showWatchlistError(watchlistItems) {
        watchlistItems.innerHTML = `
            <div class="alert alert-error shadow-lg">
                <i class="fas fa-exclamation-circle"></i>
                <span>Error loading watchlist data</span>
                <button class="btn btn-sm btn-ghost" onclick="window.watchlistManager.loadWatchlist()">Retry</button>
            </div>
        `;
    }
    
    addSymbol() {
        const symbolInput = document.getElementById('newSymbol');
        const symbolError = document.getElementById('symbolError');
        const symbol = symbolInput.value.trim().toUpperCase();
        
        // Clear previous error
        symbolError.classList.add('hidden');
        symbolError.textContent = '';
        
        if (!symbol) {
            symbolError.textContent = 'Please enter a symbol';
            symbolError.classList.remove('hidden');
            return;
        }
        
        // Show loading state
        const addBtn = document.getElementById('addSymbolBtn');
        const originalContent = addBtn.innerHTML;
        addBtn.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';
        addBtn.disabled = true;
        
        // Send request to add symbol
        fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbol: symbol }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                symbolError.textContent = data.error;
                symbolError.classList.remove('hidden');
            } else {
                // Clear input
                symbolInput.value = '';
                // Reload watchlist
                this.loadWatchlist();
            }
        })
        .catch(error => {
            console.error('Error adding symbol:', error);
            symbolError.textContent = 'Error adding symbol. Please try again.';
            symbolError.classList.remove('hidden');
        })
        .finally(() => {
            // Restore button
            addBtn.innerHTML = originalContent;
            addBtn.disabled = false;
        });
    }
    
    removeSymbol(symbolId, symbolElement) {
        // Animate removal
        symbolElement.classList.add('animate-fade-out');
        setTimeout(() => {
            symbolElement.style.height = symbolElement.offsetHeight + 'px';
            setTimeout(() => {
                symbolElement.style.height = '0';
                symbolElement.style.opacity = '0';
                symbolElement.style.margin = '0';
                symbolElement.style.padding = '0';
                symbolElement.style.overflow = 'hidden';
                setTimeout(() => symbolElement.remove(), 300);
            }, 10);
        }, 100);
        
        // Remove from database
        fetch(`${this.baseUrl}/${symbolId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (!response.ok) {
                console.error('Error removing symbol:', response.statusText);
                // If failed, reload the watchlist to restore the removed item
                this.loadWatchlist(); 
            }
        })
        .catch(error => {
            console.error('Error removing symbol:', error);
            // If failed, reload the watchlist to restore the removed item
            this.loadWatchlist();
        });
    }
}
