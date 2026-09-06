# HuNavSim + PMB2 + Nav2 動作確認ログ

- **確認日**: 2026年9月7日
- **環境**: WSL2 (Ubuntu 22.04 / ROS 2 Humble)
- **対象パッケージ**: `hunav_gazebo_wrapper`, `pmb2_2dnav`

## 1. 動作確認済み環境変数設定
export __NV_PRIME_RENDER_OFFLOAD=0
export __GLX_VENDOR_LIBRARY_NAME=mesa
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export QT_X11_NO_MITSHM=1
export OGRE_RTT_MODE=Copy
export GAZEBO_PLUGIN_PATH=/home/hakir/ros2_ws/install/hunav_gazebo_wrapper/lib:$GAZEBO_PLUGIN_PATH
export GAZEBO_MODEL_PATH=/home/hakir/ros2_ws/install/hunav_gazebo_wrapper/share/hunav_gazebo_wrapper/models:$GAZEBO_MODEL_PATH

## 2. 変更・修正点
- `hunav_gazebo_wrapper/launch/simulation.launch.py`: `gzclient_process` の連動停止による全ノードクラッシュを防ぐため、アクションリストから `gzclient_process` を除外。

## 3. 再現・起動手順
1. 残存プロセスの強制クリーンアップ:
   `sudo killall -9 gzserver gzclient gazebo rviz2 controller_server hunav_agent_manager 2>/dev/null || true`
2. 上記環境変数を読み込んでシミュレーション起動:
   `ros2 launch hunav_gazebo_wrapper simulation.launch.py`
3. 初期位置の設定（別ターミナル）:
   `ros2 topic pub --once --qos-durability transient_local /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"`
4. RViz2 で `RobotModel` にチェックを入れ、`Nav2 Goal` を送信。
