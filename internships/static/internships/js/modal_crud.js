// Attendre que le DOM soit entièrement chargé
document.addEventListener('DOMContentLoaded', function() {

    // Cibler la modale CRUD (assurez-vous que l'ID #crudModal correspond à celui de partials/crud_modal.html)
    const crudModal = document.getElementById('crudModal');

    // Écouter l'événement de Bootstrap qui se déclenche juste avant l'affichage de la modale
    crudModal.addEventListener('show.bs.modal', function (event) {
        // Bouton qui a déclenché la modale
        const button = event.relatedTarget;
        // Extraire l'URL et le titre du bouton via les attributs data-*
        const url = button.getAttribute('data-url');
        const title = button.getAttribute('data-title') || 'Opération CRUD'; // Titre par défaut

        // Mettre à jour le titre de la modale
        const modalTitle = crudModal.querySelector('.modal-title');
        modalTitle.textContent = title;

        // Charger le contenu (le formulaire ou la confirmation) via AJAX
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest' // Indiquer au backend que c'est une requête AJAX
            }
        })
        .then(response => {
             // Vérifier si la réponse est OK (statut 200-299)
            if (!response.ok) {
                // Gérer les erreurs HTTP (ex: 404, 500)
                console.error('Erreur lors du chargement du contenu de la modale:', response.status, response.statusText);
                // Afficher un message d'erreur dans la modale
                 return response.text().then(text => {
                     crudModal.querySelector('.modal-body').innerHTML = '<div class="alert alert-danger">Impossible de charger le contenu: ' + response.status + ' ' + response.statusText + (text ? '<br>' + text : '') + '</div>';
                     throw new Error('Erreur HTTP'); // Propager l'erreur
                 });
            }
            return response.text(); // Récupérer le HTML sous forme de texte
        })
        .then(html => {
            // Insérer le HTML reçu dans le corps de la modale
            const modalBody = crudModal.querySelector('.modal-body');
            modalBody.innerHTML = html;

            // --- Gérer la soumission du formulaire à l'intérieur de la modale ---
            const form = modalBody.querySelector('form');
            if (form) { // S'assurer qu'un formulaire a été chargé
                form.addEventListener('submit', function(submitEvent) {
                    submitEvent.preventDefault(); // Empêcher la soumission par défaut du formulaire

                    // URL vers laquelle envoyer les données du formulaire (peut être l'action du formulaire ou data-url du bouton)
                    const postUrl = form.getAttribute('action') || url;
                    const method = form.getAttribute('method') || 'POST'; // Méthode HTTP

                    // Récupérer les données du formulaire
                    const formData = new FormData(form);

                    // Ajouter le jeton CSRF aux données (très important pour Django)
                    // On le récupère soit d'un champ caché dans le formulaire, soit d'un cookie
                    // La méthode ci-dessous cherche un champ caché nommé 'csrfmiddlewaretoken'
                    const csrfToken = formData.get('csrfmiddlewaretoken');


                    fetch(postUrl, {
                        method: method, // POST ou la méthode spécifiée dans le formulaire
                        headers: {
                             // Indiquer au backend que c'est une requête AJAX
                            'X-Requested-With': 'XMLHttpRequest',
                            // Pour les requêtes POST avec FormData, Django ne nécessite pas
                            // le header 'Content-Type', le navigateur le gère automatiquement
                            // avec la bonne boundary.
                            // Le token CSRF est envoyé dans le FormData.
                        },
                        body: formData // Envoyer les données du formulaire
                    })
                    .then(response => {
                        // Django renvoie 200 OK avec le HTML du formulaire + erreurs si validation échoue
                        // Django renvoie 200 OK ou 204 No Content ou JsonResponse({'success': True}) si succès
                        // Django renvoie 400 Bad Request avec le HTML du formulaire + erreurs si validation échoue (si géré comme dans notre vue)
                        // Django renvoie 500 Internal Server Error en cas d'erreur serveur

                        if (response.ok) { // Statut 200-299 (inclut 200 OK, 204 No Content)
                             // Vérifier si la réponse est une réponse JSON de succès
                             const contentType = response.headers.get("content-type");
                             if (contentType && contentType.indexOf("application/json") !== -1) {
                                 return response.json().then(data => {
                                     if (data.success) {
                                         // Succès : fermer la modale et rafraîchir la page ou la liste
                                         const modal = bootstrap.Modal.getInstance(crudModal); // Obtenir l'instance de la modale
                                         modal.hide(); // Cacher la modale
                                         // Option A: Recharger la page entière (le plus simple)
                                         window.location.reload();
                                         // Option B: Mettre à jour une partie de la page (plus complexe, nécessite plus de JS/templates partiels)
                                         // Par exemple, refetch la liste des enseignants et remplacer le tbody
                                     } else {
                                         // Succès, mais la réponse JSON indique une logique non réussie (rare ici)
                                         console.error("Opération réussie mais logique non-succès:", data);
                                         // Afficher un message d'erreur si data.message existe
                                     }
                                 });
                             } else {
                                 // Réponse OK mais pas JSON (ex: 204 No Content pour suppression)
                                 const modal = bootstrap.Modal.getInstance(crudModal);
                                 modal.hide();
                                 window.location.reload(); // Recharger la page
                             }

                        } else if (response.status === 400) {
                             // Erreur de validation ou autre Bad Request
                             return response.text().then(htmlWithErrors => {
                                 // Afficher le formulaire avec les erreurs dans la modale
                                 modalBody.innerHTML = htmlWithErrors;
                                 // Réattacher l'écouteur de soumission au NOUVEAU formulaire chargé
                                 const updatedForm = modalBody.querySelector('form');
                                  if (updatedForm) {
                                       // IMPORTANT: Cloner et remplacer le formulaire pour supprimer les anciens écouteurs
                                       const newForm = updatedForm.cloneNode(true);
                                       updatedForm.parentNode.replaceChild(newForm, updatedForm);
                                       // Réattacher l'écouteur au nouveau formulaire cloné
                                       newForm.addEventListener('submit', arguments.callee); // Utilise arguments.callee pour reférer à la fonction actuelle
                                  }
                             });
                         }
                        else {
                            // Autre erreur HTTP (404, 500, etc.)
                            console.error('Erreur HTTP lors de la soumission du formulaire:', response.status, response.statusText);
                            // Afficher un message d'erreur générique
                            modalBody.innerHTML = '<div class="alert alert-danger">Une erreur est survenue. Veuillez réessayer.</div>';
                         }
                    })
                    .catch(error => {
                        console.error('Erreur lors de la soumission du formulaire:', error);
                         // Afficher un message d'erreur réseau ou autre
                        modalBody.innerHTML = '<div class="alert alert-danger">Erreur réseau ou autre problème: ' + error + '</div>';
                    });
                });
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement du contenu AJAX de la modale:', error);
            // Afficher un message d'erreur si le chargement initial échoue
            crudModal.querySelector('.modal-body').innerHTML = '<div class="alert alert-danger">Erreur lors du chargement du contenu de la modale.</div>';
        });
    });

    // Écouter l'événement de Bootstrap qui se déclenche après la fermeture de la modale
    crudModal.addEventListener('hidden.bs.modal', function () {
        // Nettoyer le contenu de la modale pour éviter d'afficher l'ancien formulaire lors de la prochaine ouverture
        crudModal.querySelector('.modal-title').textContent = '...';
        crudModal.querySelector('.modal-body').innerHTML = 'Chargement...'; // Ou un spinner
    });

});