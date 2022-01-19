import pickle
from pathlib import Path
from random import choice, shuffle
from tkinter import Canvas, NSEW, Tk, W, Frame, Button, messagebox, Label, simpledialog

from tp4.jeton import Jeton
from tp4.joueur import Joueur
from tp4.plateau import Plateau
from tp4.utils import dessiner_jeton

BASE_DIR = Path(__file__).resolve().parent


class Scrabble(Tk):
    """
    Classe Scrabble qui implémente aussi une partie de la logique de jeu.
    En dérivant de la classe tkinter.Tk, la classe Scrabble gère aussi la fenêtre principale de l'interface graphique

    Attributes:
        dictionnaire (list): Contient tous les mots qui peuvent être joués sur dans cette partie.
                             (afin de savoir si un mot est permis, on va vérifier s'il est dans dictionnaire)
        plateau (Plateau): Un objet de la classe Plateau. On y place des jetons et il nous dit le nombre de points
                           gagnés.
        jetons_libres (list): La liste de tous les jetons dans le sac (instances de la classe Jeton), c'est là que
                              chaque joueur pige des jetons quand il en a besoin.
        joueurs: (list): L'ensemble des joueurs de la partie (instances de la classe Joueur)
        joueur_actif (Joueur): Le joueur qui est en train de jouer le tour en cours. Si aucun joueur alors None.
        nb_pixels_par_case (int): Nombre de pixel qu'occupe la représentation graphique d'une case.
        chevalet (tkinter.Canvas): Rendu graphique du chevalet du joueur actif.
        position_selection_chevalet (int): Mémorise la position du jeton sélectionné sur le chevalet
                                            (vaut None si aucun jeton n'est sélectionné)
    """

    def __init__(self):
        """
        Constructeur
        """
        super().__init__()

        self.title('Scrabble')

        self.creation_board()

        self.demander_infos_partie()

    def creation_board(self):
        """
        Méthode qui sert à créer le tableau Scrabble au complet.
        Utile quand on recommence une partie pour réinitialiser le board
        """

        # Supprimer le board pour le reconstruire par la suite. Nécessaire car sinon le nouveau board se construit par-dessus l'ancien
        for board in self.grid_slaves():
            if int(board.grid_info()['row']) == 0 and int(board.grid_info()['column']) == 0:
                board.destroy()
        for chevalet in self.grid_slaves():
            if int(chevalet.grid_info()['row']) == 1 and int(chevalet.grid_info()['column']) == 0:
                chevalet.destroy()

        self.nb_pixels_par_case = 50

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.plateau = Plateau(self, self.nb_pixels_par_case)
        self.plateau.grid(row=0, column=0, sticky=NSEW)

        self.chevalet = Canvas(self, height=self.nb_pixels_par_case, width=7 * self.nb_pixels_par_case, bg='#645b4b')
        self.chevalet.grid(row=1, column=0, sticky=W)

        self.position_selection_chevalet = None

        # Création des boutons
        paneau_bouton = Frame(self)
        paneau_bouton.grid(row=1, column=1)

        bouton = Button(paneau_bouton, text="Mélanger le chevalet", command=self.clic_melanger_chevalet)
        bouton.grid(row=0, column=0, pady=5)

        bouton = Button(paneau_bouton, text="Jouer", command=self.jouer_un_tour, padx=42)
        bouton.grid(row=1, column=0, pady=5)

        bouton_passer = Button(paneau_bouton, text="Passer le tour", command=self.passer, padx=20)
        bouton_passer.grid(row=0, column=1, padx=50, pady=20)

        bouton_nouveau = Button(paneau_bouton, text="Nouvelle partie", command=self.nouvelle_partie, padx=20)
        bouton_nouveau.grid(row=1, column=1, padx=50, pady=20)

        # Associe les évènements aux méthodes correspondantes
        self.plateau.tag_bind('case', '<Button-1>', self.clic_case_plateau)
        self.chevalet.tag_bind('lettre', '<Button-1>', self.clic_lettre_chevalet)
        self.bind('<Button-3>', self.reinitialiser_tour)
        self.bind('<Escape>', self.reinitialiser_tour)

    def creation_tableau_score(self):
        """
        La méthode pour créer le tableau des scores ainsi que le joueur actif.
        La méthode supprime complètement le frame de tableau des scores ainsi que le label joueur actif à chaque appel.
        Ceci est fait pour permettre de supprimer le tableau si une nouvelle partie contient moins de joueurs que la partie précédente.
        """
        # Supprimer le tableau des scores situé à cette position dans la grid
        for label in self.grid_slaves():
            if int(label.grid_info()['row']) == 0 and int(label.grid_info()['column']) == 1:
                label.destroy()
        for label in self.grid_slaves():
            if int(label.grid_info()['row']) == 2 and int(label.grid_info()['column']) == 1:
                label.destroy()

        # Création du tableau des scores et le label joueur actif
        label_actif = Label(self, text="Voici le joueur actif: " + self.joueur_actif.nom)
        label_actif.grid(row=2, column=1, padx=50, pady=50)
        frame_score = Frame(self)
        frame_score.grid(row=0, column=1, padx=50)
        for n in range(len(self.joueurs)):
            if self.joueurs[n] == self.determiner_gagnant() and self.joueurs[n].points != 0:
                Label(frame_score, text=self.joueurs[n].nom + "\n\n\nPrésentement en tête!").grid(row=n, column=0)
                Label(frame_score, text="Score: " + str(self.joueurs[n].points)).grid(row=n, column=1, pady=50)
            else:
                Label(frame_score, text=self.joueurs[n].nom).grid(row=n, column=0)
                Label(frame_score, text="Score: " + str(self.joueurs[n].points)).grid(row=n, column=1, pady=50)

    def afficher_gagnant(self):
        """
        Méthode pour afficher le gagnant avec un popup.
        Appeler cette méthode permet de partir une nouvelle partie après le popup.
        """
        messagebox.showinfo(title="Gagnant", message="Le gagnant est: " + str(self.determiner_gagnant().nom) +
                                                     ", avec " + str(
            self.determiner_gagnant().points) + " points. Bravo!")
        self.nouvelle_partie()

    def passer(self):
        """
        Permet de passer le tour et d'aller au joueur suivant.
        Si le joueur a placé des jetons, ils seront remis dans son chevalet avant de passer.
        """
        self.reinitialiser_tour()
        self.joueur_suivant()
        self.creation_tableau_score()

    def demander_infos_partie(self):
        """
        Début d'une nouvelle partie: le jeu demande le nombre de joueurs ainsi que la langue.
        Cette méthode initialise le jeu et crée le tableau des scores
        """
        # Gestion d'entrée pour la langue
        valide = False
        while not valide:
            prompt_langue = simpledialog.askstring("Langue", "Entrez la langue (FR/EN)")
            try:
                if prompt_langue.upper() not in ['FR', 'EN']:
                    raise LangueInvalideException("Langue non supportée")
                valide = True
            except:
                messagebox.showerror(title="Erreur", message="Langue non supportée. La langue doit être soit FR ou EN.")

        # Gestion d'entrée pour le nombre de joueurs
        valide = False
        while not valide:
            prompt_joueurs = simpledialog.askinteger("Nombre de joueurs", "Entrez le nombre de joueurs")
            try:
                if prompt_joueurs not in range(2, 5):
                    raise NombreDeJoueursException("nombre de joueurs invalide")
                valide = True
            except:
                messagebox.showerror(title="Erreur", message="Le nombre de joueurs doit être entre 2 et 4.")

        self.initialiser_jeu(prompt_joueurs, prompt_langue)
        self.creation_tableau_score()

    def nouvelle_partie(self):
        """
        Cette méthode réinitialise le board et recommence la partie en redemandant les infos de départ.
        """
        self.creation_board()
        self.demander_infos_partie()

    def initialiser_jeu(self, nb_joueurs=2, langue='fr'):
        """
        Étant donné un nombre de joueurs et une langue, cette méthode crée une partie de scrabble.

        Pour une nouvelle partie de scrabble:
        - La liste des joueurs est créée et chaque joueur porte automatiquement le nom Joueur 1, Joueur 2, ... Joueur n,
          où n est le nombre de joueurs;
        - Le joueur_actif est None.

        Args:
            nb_joueurs (int): nombre de joueurs de la partie (au minimun 2 au maximum 4).
            langue (str): 'FR' pour la langue française et 'EN' pour la langue anglaise. Charge en mémoire les mots
                          contenus dans le fichier "dictionnaire_francais.txt" ou "dictionnaire_anglais.txt".
            La langue détermine aussi les jetons de départ.
            Voir https://fr.wikipedia.org/wiki/Lettres_du_Scrabble
            Note: Dans notre scrabble, nous n'utiliserons pas les jetons blancs (jokers) qui ne contiennent aucune lettre.

        Raises:
            LangueInvalideException:
                - Si la langue n'est ni 'fr', 'FR', 'en', ou 'EN'.
            NombreDeJoueursException:
                - Si le nombre de joueurs n'est pas compris entre 2 et 4 (2 et 4 étant inclus).
        """
        if not (langue.upper() in ['FR', 'EN']):
            raise LangueInvalideException('Langue non supportée.')
        if not (2 <= nb_joueurs <= 4):
            raise NombreDeJoueursException('Il faut entre 2 et 4 personnes pour jouer.')

        self.joueur_actif = None
        self.joueurs = [Joueur(f'Joueur {i + 1}') for i in range(nb_joueurs)]

        if langue.upper() == 'FR':
            # Infos disponibles sur https://fr.wikipedia.org/wiki/Lettres_du_Scrabble
            data = [('E', 15, 1), ('A', 9, 1), ('I', 8, 1), ('N', 6, 1), ('O', 6, 1),
                    ('R', 6, 1), ('S', 6, 1), ('T', 6, 1), ('U', 6, 1), ('L', 5, 1),
                    ('D', 3, 2), ('M', 3, 2), ('G', 2, 2), ('B', 2, 3), ('C', 2, 3),
                    ('P', 2, 3), ('F', 2, 4), ('H', 2, 4), ('V', 2, 4), ('J', 1, 8),
                    ('Q', 1, 8), ('K', 1, 10), ('W', 1, 10), ('X', 1, 10), ('Y', 1, 10),
                    ('Z', 1, 10)]
            chemin_fichier_dictionnaire = BASE_DIR / 'dictionnaire_francais.txt'
        elif langue.upper() == 'EN':
            # Infos disponibles sur https://fr.wikipedia.org/wiki/Lettres_du_Scrabble
            data = [('E', 12, 1), ('A', 9, 1), ('I', 9, 1), ('N', 6, 1), ('O', 8, 1),
                    ('R', 6, 1), ('S', 4, 1), ('T', 6, 1), ('U', 4, 1), ('L', 4, 1),
                    ('D', 4, 2), ('M', 2, 3), ('G', 3, 2), ('B', 2, 3), ('C', 2, 3),
                    ('P', 2, 3), ('F', 2, 4), ('H', 2, 4), ('V', 2, 4), ('J', 1, 8),
                    ('Q', 1, 10), ('K', 1, 5), ('W', 2, 4), ('X', 1, 8), ('Y', 2, 4),
                    ('Z', 1, 10)]
            chemin_fichier_dictionnaire = BASE_DIR / 'dictionnaire_anglais.txt'

        self.jetons_libres = [Jeton(lettre, valeur) for lettre, occurences, valeur in data for i in range(occurences)]
        with open(chemin_fichier_dictionnaire, 'r') as f:
            self.dictionnaire = [x[:-1].upper() for x in f.readlines() if len(x[:-1]) > 1]

        self.joueur_suivant()

    def clic_melanger_chevalet(self, event=None):
        """
        Modifie aléatoirement l'ordre des jetons sur le chevalet du joueur actif.

        Args:
            event (tkinter.Event): L'évènement ayant causé l'appel de la méthode (non utilisé).
        """
        self.reinitialiser_tour()
        self.joueur_actif.melanger_jetons()
        self.dessiner_chevalet()

    def reinitialiser_tour(self, event=None):
        """
        Lorsque le joueur actif a déplacé des jetons de son chevalet au plateau, cette méthode replace
        ces jetons sur le chevalet.

        Args:
            event (tkinter.Event): L'évènement ayant causé l'appel de la méthode (non utilisé).
        """
        liste_jetons = self.plateau.retirer_jetons_en_jeu()[0]
        for jeton in liste_jetons:
            self.joueur_actif.ajouter_jeton(jeton)

        self.position_selection_chevalet = None
        self.plateau.dessiner()
        self.dessiner_chevalet()

    def clic_lettre_chevalet(self, event):
        """
        Gère la sélection d'un jeton sur le chevalet du joueur actif.

        Args:
            event (tkinter.Event): L'évènement ayant causé l'appel de la méthode.
        """
        self.position_selection_chevalet = event.x // self.nb_pixels_par_case
        self.dessiner_chevalet()

    def clic_case_plateau(self, event):
        """
        Gère le déplacement d'un jeton à partir du chevalet jusqu'au plateau.

        Args:
            event (tkinter.Event): L'évènement ayant causé l'appel de la méthode.
        """
        if self.position_selection_chevalet is None:
            return

        jeton = self.joueur_actif.retirer_jeton(self.position_selection_chevalet)

        if self.plateau.ajouter_jeton_en_jeu(jeton, event.x, event.y):
            self.position_selection_chevalet = None
            self.plateau.dessiner()
            self.dessiner_chevalet()
        else:
            self.joueur_actif.ajouter_jeton(self.position_selection_chevalet)

    def mot_permis(self, mot):
        """
        Permet de savoir si un mot est permis dans la partie ou pas 
        en vérifiant dans le dictionnaire.

        Args:
            mot (str): Mot à vérifier.

        Returns:
            bool: True si le mot est dans le dictionnaire, False sinon.
        """
        return mot.upper() in self.dictionnaire

    def determiner_gagnant(self):
        """
        Détermine le joueur gagnant.
        Le joueur gagnant doit avoir un pointage supérieur ou égal à celui des autres.

        Returns:
            Joueur: Le joueur gagnant. Si plusieurs sont à égalité, on en retourne un seul parmi ceux-ci.
        """
        return max(self.joueurs, key=lambda j: j.points)

    def partie_terminee(self):
        """
        Vérifie si la partie est terminée. Une partie est terminée si il n'existe plus de jetons libres ou il reste
        moins de deux (2) joueurs. C'est la règle que nous avons choisi d'utiliser pour ce travail, donc essayez de
        négliger les autres que vous connaissez ou avez lu sur Internet.

        Returns:
            bool: True si la partie est terminée, et False autrement.
        """
        return len(self.jetons_libres) == 0 or len(self.joueurs) < 2

    def joueur_suivant(self):
        """
        Change le joueur actif.
        Le nouveau joueur actif est celui à l'index du (joueur courant + 1) % nb_joueurs.
        Si on n'a aucun joueur actif, on détermine au hasard le suivant.
        """
        if self.joueur_actif is None:
            self.joueur_actif = choice(self.joueurs)
        else:
            self.joueur_actif = self.joueurs[(self.joueurs.index(self.joueur_actif) + 1) % len(self.joueurs)]

        if self.joueur_actif.nb_a_tirer() > 0:
            for jeton in self.tirer_jetons(self.joueur_actif.nb_a_tirer()):
                self.joueur_actif.ajouter_jeton(jeton)

        self.position_selection_chevalet = None
        self.dessiner_chevalet()

    def dessiner_chevalet(self):
        """
        Dessine le chevalet du joueur actif sur l'interface graphique.
        """
        self.chevalet.delete('lettre')

        for j, jeton in enumerate(self.joueur_actif.chevalet):
            if jeton is not None:
                selection = j == self.position_selection_chevalet
                dessiner_jeton(self.chevalet, jeton, 0, j, self.nb_pixels_par_case, selection)

    def tirer_jetons(self, n):
        """
        Simule le tirage de n jetons du sac à jetons et renvoie ceux-ci. Il s'agit de prendre au hasard des jetons dans
        self.jetons_libres et de les retourner.

        Args:
            n (int): Le nombre de jetons à tirer.

        Returns:
            list: La liste des jetons tirés (instances de la classe Jeton).

        Raises:
            NombreJetonException: Si n n'est pas compris dans l'intervalle [0, nombre total de jetons libres].
        """
        if not (0 <= n <= len(self.jetons_libres)):
            raise NombreJetonException('n doit être compris entre 0 et le nombre total de jetons libres.')

        shuffle(self.jetons_libres)
        res = self.jetons_libres[:n]
        self.jetons_libres = self.jetons_libres[n:]
        return res

    def jouer_un_tour(self):
        """
        Vérifie d'abord si les positions des jetons déposés sur le plateau par le joueur actif sont valides.
        Si c'est le cas, le tour est joué.
        """

        liste_jetons, liste_positions = self.plateau.retirer_jetons_en_jeu()

        # Vérifier si les emplacements des jetons sont valides
        if len(liste_positions) == 0:
            messagebox.showerror('Oups!', "Aucun jeton n'est placé sur le plateau.")
            self.reinitialiser_tour()
        elif not self.plateau.valider_positions_avant_ajout(liste_positions):
            messagebox.showerror('Oups!', "La position des lettres n'est pas valide.")
            for jeton in liste_jetons:
                self.joueur_actif.ajouter_jeton(jeton)
            self.reinitialiser_tour()
        else:
            mots, score = self.plateau.placer_mots(liste_jetons, liste_positions)

            # Vérifier si les mots créés existent dans le dictionnaire choisi préalablement
            if any([not self.mot_permis(m) for m in mots]):
                messagebox.showerror('Oups!', "Au moins l'un des mots formés est absent du dictionnaire.")
                for pos in liste_positions:
                    self.plateau.retirer_jeton(pos)
                for jeton in liste_jetons:
                    self.joueur_actif.ajouter_jeton(jeton)
                self.reinitialiser_tour()
            else:
                messagebox.showinfo('Bravo!', f'Mots formés: {mots}\nScore obtenu: {score}')
                self.joueur_actif.ajouter_points(score)
                liste_jetons = []
                self.joueur_suivant()

        # Update du tableau des scores
        self.creation_tableau_score()

        # Vérifier si la partie est terminée, si oui, afficher le gagnant.
        if self.partie_terminee():
            self.afficher_gagnant()

    def sauvegarder_partie(self, nom_fichier):
        """
        Permet de sauvegarder l'objet courant dans le fichier portant le nom spécifié.
        La sauvegarde se fera grâce à la fonction dump du module pickle.

        Args:
            nom_fichier (str): Nom du fichier qui contient un objet scrabble.

        Returns:
            bool: True si la sauvegarde s'est bien déroulée,
                  False si une erreur est survenue durant la sauvegarde.
        """
        try:
            with open(nom_fichier, 'wb') as f:
                pickle.dump(self, f)
        except:
            return False

        return True


def charger_partie(nom_fichier):
    """
    Fonction permettant de créer un objet scrabble en lisant le fichier dans lequel l'objet avait été sauvegardé
    précédemment.

    Args:
        nom_fichier (str): Nom du fichier qui contient un objet scrabble.

    Returns
        Scrabble: L'objet chargé en mémoire.
    """
    with open(nom_fichier, 'rb') as f:
        return pickle.load(f)


class NombreDeJoueursException(Exception):
    pass


class LangueInvalideException(Exception):
    pass


class NombreJetonException(Exception):
    pass
