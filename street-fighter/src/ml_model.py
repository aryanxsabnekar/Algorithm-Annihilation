import numpy as np
from sklearn.tree import DecisionTreeClassifier
import pickle
import csv
import os


class PlayerBehaviorTracker:
    def __init__(self):
        self.data=[]
        self.current_player="player_1"

    def set_player(self,player_name):
        """Set the active player for saving behavior data and reset data storage."""
        self.current_player=player_name
        self.data=[]

    def log(self,state,action):
        features=self.extract_features(state)
        self.data.append((features,action))

    def extract_features(self,state):
        player_x=state.get("player_x",0)
        player_y=state.get("player_y",0)
        cpu_x=state.get("cpu_x",0)
        cpu_y=state.get("cpu_y",0)
        rel_dist = abs(cpu_x-player_x)
        return [player_x,player_y,cpu_x,cpu_y,rel_dist,state.get("player_velocity",0)]

    def get_training_data(self):
        if not self.data:
            return None,None
        X=np.array([d[0] for d in self.data])
        y=np.array([d[1] for d in self.data])
        return X,y

    def save_to_csv(self):
        """Appends behavior data to a CSV file for the current player."""
        filename=f"{self.current_player}_behavior_log.csv"
        file_exists=os.path.isfile(filename)
        with open(filename,mode="a",newline="") as file:
            writer=csv.writer(file)
            if not file_exists:
                writer.writerow(["player_x","player_y","cpu_x","cpu_y","rel_dist","velocity","action"])
            for features,action in self.data:
                writer.writerow(features+[action])

    def load_training_data(self):
        """Loads training data from the CSV file of the current player."""
        filename=f"{self.current_player}_behavior_log.csv"
        try:
            with open(filename,mode="r") as file:
                reader=csv.reader(file)
                next(reader)
                self.data=[]
                for row in reader:
                    features=list(map(float,row[:-1])) #convert feature values to float
                    action=row[-1]
                    self.data.append((features,action))
        except FileNotFoundError:
            print(f"No training data found for {self.current_player}. Starting fresh.")


class MLModel:
    def __init__(self):
        self.model=DecisionTreeClassifier()
        self.trained=False

    def train(self,X,y):
        self.model.fit(X,y)
        self.trained=True

    def predict(self,features):
        if not self.trained:
            return None
        pred=self.model.predict(features.reshape(1,-1))
        return pred[0]

    def save(self,filename):
        with open(filename,"wb") as f:
            pickle.dump(self.model,f)

    def load(self,filename):
        with open(filename,"rb") as f:
            self.model=pickle.load(f)
            self.trained=True

def extract_features_from_state(target,cpu):
    """
    Extracts a feature vector from the current state.
    Features: [player_x, player_y, cpu_x, cpu_y, relative_distance, player_velocity]
    """
    player_x=target.rect.x
    player_y=target.rect.y
    cpu_x=cpu.rect.x
    cpu_y=cpu.rect.y
    rel_dist=abs(cpu_x-player_x)
    player_velocity=10 if target.running else 0
    return np.array([player_x,player_y,cpu_x,cpu_y,rel_dist,player_velocity])

# Global instances used throughout the game
cpu_model=MLModel()
behavior_tracker=PlayerBehaviorTracker()