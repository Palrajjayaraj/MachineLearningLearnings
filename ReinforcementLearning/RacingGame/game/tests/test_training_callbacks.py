import unittest
import os
import tempfile
import shutil
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from src.gym_env import RacingGameEnv
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from train import CheckpointCallback


class TestCheckpointCallback(unittest.TestCase):
    """
    Test suite for checkpoint callback functionality.
    """
    
    def setUp(self):
        """Set up temporary directory for test checkpoints."""
        self.temp_dir = tempfile.mkdtemp()
        self.checkpoint_path = os.path.join(self.temp_dir, "test_model")
        
    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_checkpoint_callback_initialization(self):
        """Test that CheckpointCallback initializes correctly."""
        callback = CheckpointCallback(
            save_freq=1000,
            save_path=self.checkpoint_path,
            verbose=1
        )
        
        self.assertEqual(callback.save_freq, 1000)
        self.assertEqual(callback.save_path, self.checkpoint_path)
        self.assertEqual(callback.checkpoint_count, 0)
    
    def test_checkpoint_creation(self):
        """Test that checkpoints are created at correct intervals."""
        # Create a simple environment
        env = make_vec_env(lambda: RacingGameEnv(frame_skip=4), n_envs=1)
        
        # Create a small model for testing
        model = PPO("MlpPolicy", env, verbose=0)
        
        # Create callback with small save frequency for testing
        callback = CheckpointCallback(
            save_freq=100,  # Save every 100 steps
            save_path=self.checkpoint_path,
            verbose=0
        )
        
        # Train for a short time to trigger checkpoints
        model.learn(total_timesteps=250, callback=callback)
        
        # Check that at least one checkpoint was created
        # With 250 steps and save_freq=100, we should have 2 checkpoints
        checkpoint_1 = f"{self.checkpoint_path}_checkpoint_1.zip"
        checkpoint_2 = f"{self.checkpoint_path}_checkpoint_2.zip"
        
        self.assertTrue(os.path.exists(checkpoint_1), 
                       f"First checkpoint should exist at {checkpoint_1}")
        self.assertTrue(os.path.exists(checkpoint_2), 
                       f"Second checkpoint should exist at {checkpoint_2}")
        
        env.close()
    
    def test_checkpoint_loading(self):
        """Test that saved checkpoints can be loaded successfully."""
        # Create environment
        env = make_vec_env(lambda: RacingGameEnv(frame_skip=4), n_envs=1)
        
        # Create and train a model
        model = PPO("MlpPolicy", env, verbose=0)
        callback = CheckpointCallback(
            save_freq=100,
            save_path=self.checkpoint_path,
            verbose=0
        )
        model.learn(total_timesteps=150, callback=callback)
        
        # Try to load the checkpoint
        checkpoint_path = f"{self.checkpoint_path}_checkpoint_1.zip"
        self.assertTrue(os.path.exists(checkpoint_path))
        
        # Load the model
        loaded_model = PPO.load(checkpoint_path, env=env)
        self.assertIsNotNone(loaded_model)
        
        # Verify the model can make predictions
        obs = env.reset()
        action, _ = loaded_model.predict(obs)
        self.assertIsNotNone(action)
        
        env.close()
    
    def test_checkpoint_file_size(self):
        """Test that checkpoint files are created with reasonable size."""
        env = make_vec_env(lambda: RacingGameEnv(frame_skip=4), n_envs=1)
        
        model = PPO("MlpPolicy", env, verbose=0)
        callback = CheckpointCallback(
            save_freq=50,
            save_path=self.checkpoint_path,
            verbose=0
        )
        model.learn(total_timesteps=100, callback=callback)
        
        checkpoint_path = f"{self.checkpoint_path}_checkpoint_1.zip"
        self.assertTrue(os.path.exists(checkpoint_path))
        
        # Check file size is reasonable (should be > 1KB and < 100MB)
        file_size = os.path.getsize(checkpoint_path)
        self.assertGreater(file_size, 1024, "Checkpoint file should be > 1KB")
        self.assertLess(file_size, 100 * 1024 * 1024, "Checkpoint file should be < 100MB")
        
        env.close()


class TestModelSaving(unittest.TestCase):
    """
    Test suite for model saving and loading functionality.
    """
    
    def setUp(self):
        """Set up temporary directory for test models."""
        self.temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.temp_dir, "test_model")
        
    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_interrupted_model_save(self):
        """Test that interrupted model can be saved and loaded."""
        env = make_vec_env(lambda: RacingGameEnv(frame_skip=4), n_envs=1)
        
        # Create and train model
        model = PPO("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=100)
        
        # Simulate interrupted save
        interrupted_path = f"{self.model_path}_interrupted"
        model.save(interrupted_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(f"{interrupted_path}.zip"))
        
        # Load and verify
        loaded_model = PPO.load(f"{interrupted_path}.zip", env=env)
        self.assertIsNotNone(loaded_model)
        
        env.close()
    
    def test_final_model_save(self):
        """Test that final model can be saved and loaded."""
        env = make_vec_env(lambda: RacingGameEnv(frame_skip=4), n_envs=1)
        
        # Create and train model
        model = PPO("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=100)
        
        # Simulate final save
        final_path = f"{self.model_path}_final"
        model.save(final_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(f"{final_path}.zip"))
        
        # Load and verify
        loaded_model = PPO.load(f"{final_path}.zip", env=env)
        self.assertIsNotNone(loaded_model)
        
        env.close()
    
    def test_model_resume_training(self):
        """Test that a saved model can resume training."""
        env = make_vec_env(lambda: RacingGameEnv(frame_skip=4), n_envs=1)
        
        # Create and train initial model
        model = PPO("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=100)
        
        # Save model
        model.save(self.model_path)
        
        # Load model and resume training
        loaded_model = PPO.load(f"{self.model_path}.zip", env=env)
        
        # This should not raise an error
        try:
            loaded_model.learn(total_timesteps=50)
            resume_success = True
        except Exception as e:
            resume_success = False
            print(f"Resume training failed: {e}")
        
        self.assertTrue(resume_success, "Model should be able to resume training")
        
        env.close()


if __name__ == '__main__':
    unittest.main()
