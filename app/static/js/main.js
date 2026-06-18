document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('hotelSearchInput');
    const hotelCards = document.querySelectorAll('.hotel-card');
    const noResultsMessage = document.getElementById('noResultsMessage');

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase().trim();
        let visibleCount = 0;

        hotelCards.forEach(card => {
            const hotelName = card.getAttribute('data-hotel-name');
            if (hotelName.includes(searchTerm)) {
                card.classList.remove('hidden');
                visibleCount++;
            } else {
                card.classList.add('hidden');
            }
        });

        if (visibleCount === 0) {
            noResultsMessage.classList.remove('hidden');
        } else {
            noResultsMessage.classList.add('hidden');
        }
    });
});
