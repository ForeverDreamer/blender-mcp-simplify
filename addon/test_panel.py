"""
Blender MCP Test Panel - Similar to After Effects MCP Bridge Auto test panel

Provides script testing, parameter configuration, result display and other features
"""

import json
from typing import Any

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup


class BLENDERMCP_PG_TestProperties(PropertyGroup):
    """Test panel property group"""

    # Script selection
    selected_script: EnumProperty(
        name="Script",
        description="Select script to execute",
        items=[
            ("create-object", "Create Object", "Create 3D object"),
            (
                "insert-keyframe",
                "Insert Keyframe",
                "Insert keyframe for object property",
            ),
            (
                "setup-lighting-scene",
                "Setup Lighting Scene",
                "Create standard lighting setup",
            ),
            ("render-frame", "Render Frame", "Render current or specified frame"),
            ("clear-animation", "Clear Animation", "Delete object animation data"),
            (
                "get-animation-info",
                "Animation Info",
                "Get object animation information",
            ),
            ("set-frame-range", "Set Frame Range", "Set timeline frame range"),
            ("animate-along-path", "Path Animation", "Create animation along path"),
        ],
        default="create-object",
    )  # type: ignore

    # General parameters
    object_name: StringProperty(
        name="Object Name",
        description="Target object name",
        default="Cube",
    )  # type: ignore

    property_name: EnumProperty(
        name="Property",
        description="Property to operate on",
        items=[
            ("location", "Location", "Object location"),
            ("rotation_euler", "Rotation", "Object rotation"),
            ("scale", "Scale", "Object scale"),
        ],
        default="location",
    )  # type: ignore

    frame_number: IntProperty(
        name="Frame Number",
        description="Target frame number",
        default=1,
        min=1,
        max=9999,
    )  # type: ignore

    start_frame: IntProperty(
        name="Start Frame",
        description="Animation start frame",
        default=1,
        min=1,
    )  # type: ignore

    end_frame: IntProperty(
        name="End Frame",
        description="Animation end frame",
        default=100,
        min=1,
    )  # type: ignore

    # Object type
    object_type: EnumProperty(
        name="Object Type",
        description="Type of object to create",
        items=[
            ("MESH", "Mesh", "Mesh object"),
            ("CURVE", "Curve", "Curve object"),
            ("SURFACE", "Surface", "Surface object"),
            ("META", "Metaball", "Metaball object"),
            ("FONT", "Text", "Text object"),
            ("VOLUME", "Volume", "Volume object"),
        ],
        default="MESH",
    )  # type: ignore

    # Interpolation type
    interpolation: EnumProperty(
        name="Interpolation",
        description="Keyframe interpolation type",
        items=[
            ("CONSTANT", "Constant", "Constant interpolation"),
            ("LINEAR", "Linear", "Linear interpolation"),
            ("BEZIER", "Bezier", "Bezier interpolation"),
        ],
        default="BEZIER",
    )  # type: ignore

    # Custom parameters JSON
    custom_params: StringProperty(
        name="Custom Parameters",
        description="Custom parameters in JSON format",
        default="{}",
    )  # type: ignore

    # Result display
    last_result: StringProperty(
        name="Execution Result",
        description="Last execution result",
        default="",
    )  # type: ignore

    # Auto execute option
    auto_execute: BoolProperty(
        name="Auto Execute",
        description="Automatically execute script when parameters change",
        default=False,
    )  # type: ignore

    # Show detailed result
    show_detailed_result: BoolProperty(
        name="Show Detailed Result",
        description="Show complete JSON result",
        default=True,
    )  # type: ignore

    # Connection status
    connection_status: StringProperty(
        name="Connection Status",
        description="MCP server connection status",
        default="Not Connected",
    )  # type: ignore


class BLENDERMCP_OT_ExecuteTestScript(Operator):
    """Execute selected test script"""

    bl_idname = "blendermcp.execute_test_script"
    bl_label = "Execute Script"
    bl_description = "Execute selected test script"

    def execute(self, context):
        props = context.scene.blendermcp_test_props

        try:
            # Build parameters
            params = self._build_parameters(props)

            # Note: This should not connect to MCP server via HTTP
            # The correct architecture is: MCP server (src/server.py) connects to Blender internal server via socket
            # Test panel should directly test Blender internal functionality via socket connection

            # Connect directly to Blender internal server to test script execution via socket
            result = self._execute_via_socket(props.selected_script, params)
            props.connection_status = "Socket connection test (port 9876)"

            # Update results
            if props.show_detailed_result:
                props.last_result = json.dumps(result, indent=2, ensure_ascii=False)
            elif result.get("success", False):
                props.last_result = f"✓ {result.get('message', 'Execution successful')}"
            else:
                props.last_result = f"✗ {result.get('error', 'Execution failed')}"

            if result.get("success", False):
                self.report(
                    {"INFO"}, f"Script execution successful: {props.selected_script}"
                )
            else:
                self.report(
                    {"ERROR"},
                    f"Script execution failed: {result.get('error', 'Unknown error')}",
                )

        except Exception as e:
            error_msg = f"Execution error: {e!s}"
            props.last_result = error_msg
            props.connection_status = "Connection error"
            self.report({"ERROR"}, error_msg)
            return {"CANCELLED"}

        return {"FINISHED"}

    def _execute_via_socket(self, script, params):
        """Execute script directly via socket connection"""
        import socket

        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(
                120
            )  # Increased from 60 to 120 seconds for sufficient time

            print("[Test Panel] Attempting to connect to localhost:9876...")
            test_socket.connect(("localhost", 9876))
            print(
                f"[Test Panel] Connection successful, preparing to execute script: {script}"
            )

            # Simplify code execution - first test basic Blender operations, avoid complex script_registry
            # Generate simple Blender Python code based on script type
            code = self._generate_simple_script_code(script, params)

            # Send command
            command = {
                "type": "execute_code",
                "params": {
                    "code": code,
                },
            }

            command_json = json.dumps(command)
            print(f"[Test Panel] Sending command, size: {len(command_json)} bytes")
            test_socket.sendall(command_json.encode("utf-8"))

            # Receive response - improved receiving logic
            print("[Test Panel] Waiting for response (max 120 seconds)...")

            try:
                # Use larger buffer and better error handling
                response_data = b""
                while True:
                    try:
                        chunk = test_socket.recv(8192)
                        if not chunk:
                            break
                        response_data += chunk
                        # Try to parse JSON, if successful consider reception complete
                        try:
                            json.loads(response_data.decode("utf-8"))
                            break  # JSON parsing successful, data reception complete
                        except json.JSONDecodeError:
                            continue  # Continue receiving data
                    except TimeoutError:
                        if response_data:
                            break  # If there's data, try parsing
                        raise  # If no data, raise timeout exception

                print(
                    f"[Test Panel] Received response, size: {len(response_data)} bytes"
                )

                if not response_data:
                    return {
                        "success": False,
                        "error": "Server returned empty response",
                    }

                # Parse JSON response
                try:
                    response = json.loads(response_data.decode("utf-8"))
                    print(
                        f"[Test Panel] Response parsed successfully: {response.get('status', 'unknown')}"
                    )

                    # Check if response contains SCRIPT_RESULT
                    if "result" in response and isinstance(response["result"], str):
                        output = response["result"]

                        # Look for SCRIPT_RESULT marker
                        if "SCRIPT_RESULT:" in output:
                            try:
                                result_start = output.find("SCRIPT_RESULT:")
                                result_json = output[result_start + 14 :].strip()
                                script_result = json.loads(result_json)
                                return script_result
                            except (json.JSONDecodeError, ValueError) as e:
                                print(
                                    f"[Test Panel] Failed to parse SCRIPT_RESULT: {e}"
                                )
                                return {
                                    "success": False,
                                    "error": f"Failed to parse script result: {e}",
                                    "raw_output": output,
                                }
                        else:
                            return {
                                "success": True,
                                "message": f"Script '{script}' execution completed",
                                "output": output,
                            }
                    else:
                        return {
                            "success": False,
                            "error": response.get(
                                "message", "Blender server execution failed"
                            ),
                        }

                except json.JSONDecodeError as e:
                    print(f"[Test Panel] JSON parsing failed: {e}")
                    return {
                        "success": False,
                        "error": f"Failed to parse server response: {e}",
                        "raw_data": response_data.decode("utf-8", errors="ignore"),
                    }

            except Exception as e:
                print(f"[Test Panel] Failed to receive response: {e}")
                return {
                    "success": False,
                    "error": f"Failed to receive response: {e}",
                }

        except ConnectionRefusedError:
            print("[Test Panel] Connection refused - Blender server not running")
            return {
                "success": False,
                "error": "Blender server not running (port 9876) - Please start Blender internal server first",
            }
        except TimeoutError:
            print("[Test Panel] Socket connection timeout")
            return {
                "success": False,
                "error": "Socket connection timeout (120s) - Script execution took too long or server response slow",
            }
        except Exception as e:
            print(f"[Test Panel] Socket connection exception: {e}")
            return {
                "success": False,
                "error": f"Socket connection failed: {e}",
            }

    def _generate_simple_script_code(self, script, params):
        """Generate simple Blender Python code based on script type"""
        if script == "create-object":
            object_type = params.get("object_type", "MESH")
            name = params.get("name", "TestObject")

            if object_type == "MESH":
                return f"""
import bpy
print("[Blender] Starting object creation...")

# Create cube mesh
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

# Compatible way to get active object
if hasattr(bpy.context, 'active_object') and bpy.context.active_object:
    obj = bpy.context.active_object
elif hasattr(bpy.context, 'object') and bpy.context.object:
    obj = bpy.context.object
else:
    # Get last added object from scene
    obj = bpy.context.scene.objects[-1] if bpy.context.scene.objects else None

if obj:
    obj.name = "{name}"
    print(f"[Blender] Successfully created object: {{obj.name}}")
    print("SCRIPT_RESULT:", {{"success": True, "message": f"Successfully created object: {{obj.name}}", "object_name": obj.name}})
else:
    print("[Blender] Error: Cannot get created object")
    print("SCRIPT_RESULT:", {{"success": False, "error": "Cannot get created object"}})
"""

        elif script == "insert-keyframe":
            object_name = params.get("object_name", "Cube")
            property_name = params.get("property_name", "location")
            frame = params.get("frame", 1)

            return f"""
import bpy
print("[Blender] Starting keyframe insertion...")

obj = bpy.data.objects.get("{object_name}")
if obj:
    # Ensure frame is set in correct context
    if hasattr(bpy.context.scene, 'frame_set'):
        bpy.context.scene.frame_set({frame})
    else:
        bpy.context.scene.frame_current = {frame}
    
    # Select object and set as active
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    obj.keyframe_insert(data_path="{property_name}")
    print(f"[Blender] Successfully inserted keyframe for object {{obj.name}} property {property_name} at frame {frame}")
    print("SCRIPT_RESULT:", {{"success": True, "message": f"Successfully inserted keyframe: {{obj.name}}.{property_name} @ {frame}"}})
else:
    print(f"[Blender] Error: Object '{object_name}' not found")
    print("SCRIPT_RESULT:", {{"success": False, "error": "Specified object not found"}})
"""

        elif script == "setup-lighting-scene":
            return """
import bpy
print("[Blender] Starting lighting scene setup...")

# Delete existing lights
lights_to_remove = [obj for obj in bpy.data.objects if obj.type == 'LIGHT']
for obj in lights_to_remove:
    bpy.data.objects.remove(obj, do_unlink=True)

# Add key light
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
# Get newly created light
sun = None
if hasattr(bpy.context, 'active_object') and bpy.context.active_object:
    sun = bpy.context.active_object
elif hasattr(bpy.context, 'object') and bpy.context.object:
    sun = bpy.context.object
else:
    # Find latest light object from scene
    for obj in reversed(bpy.context.scene.objects):
        if obj.type == 'LIGHT':
            sun = obj
            break

if sun:
    sun.name = "Key_Light"
    sun.data.energy = 3.0

# Add fill light
bpy.ops.object.light_add(type='AREA', location=(-5, 5, 5))
# Get newly created area light
area = None
if hasattr(bpy.context, 'active_object') and bpy.context.active_object:
    area = bpy.context.active_object
elif hasattr(bpy.context, 'object') and bpy.context.object:
    area = bpy.context.object
else:
    # Find latest area light from scene
    for obj in reversed(bpy.context.scene.objects):
        if obj.type == 'LIGHT' and obj != sun:
            area = obj
            break

if area:
    area.name = "Fill_Light"
    area.data.energy = 1.0

lights_created = []
if sun:
    lights_created.append(sun.name)
if area:
    lights_created.append(area.name)

print("[Blender] Lighting scene setup complete")
print("SCRIPT_RESULT:", {"success": True, "message": "Lighting scene setup complete", "lights_created": lights_created})
"""

        elif script == "render-frame":
            frame = params.get("frame", 1)
            return f"""
import bpy
print("[Blender] Starting frame render...")

# Set current frame
if hasattr(bpy.context.scene, 'frame_set'):
    bpy.context.scene.frame_set({frame})
else:
    bpy.context.scene.frame_current = {frame}

print(f"[Blender] Rendering frame {frame} (simulation)")
print("SCRIPT_RESULT:", {{"success": True, "message": f"Frame {frame} render complete (simulation)"}})
"""

        elif script == "clear-animation":
            object_name = params.get("object_name", "Cube")
            return f"""
import bpy
print("[Blender] Starting animation clear...")

obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data:
    obj.animation_data_clear()
    print(f"[Blender] Cleared animation data for object {{obj.name}}")
    print("SCRIPT_RESULT:", {{"success": True, "message": f"Cleared animation for {{obj.name}}"}})
else:
    print(f"[Blender] Object '{object_name}' has no animation data or doesn't exist")
    print("SCRIPT_RESULT:", {{"success": True, "message": "Object has no animation data or doesn't exist"}})
"""

        else:
            return f"""
import bpy
print("[Blender] Running basic test...")

# Compatibility check
context_info = []
if hasattr(bpy.context, 'scene'):
    context_info.append(f"Scene: {{bpy.context.scene.name}}")
    context_info.append(f"Object count: {{len(bpy.context.scene.objects)}}")

if hasattr(bpy.context, 'active_object'):
    if bpy.context.active_object:
        context_info.append(f"Active object: {{bpy.context.active_object.name}}")
    else:
        context_info.append("No active object")
elif hasattr(bpy.context, 'object'):
    if bpy.context.object:
        context_info.append(f"Current object: {{bpy.context.object.name}}")
    else:
        context_info.append("No current object")

info_str = " | ".join(context_info)
print(f"[Blender] Context info: {{info_str}}")
print("SCRIPT_RESULT:", {{"success": True, "message": f"Script '{script}' execution complete (basic test)", "context_info": info_str}})
"""

    def _build_parameters(self, props) -> dict[str, Any]:
        """Build parameters based on selected script"""
        script = props.selected_script
        params = {}

        # Try to parse custom parameters
        try:
            if props.custom_params.strip():
                custom = json.loads(props.custom_params)
                params.update(custom)
        except json.JSONDecodeError:
            pass

        # Add specific parameters based on script type
        if script == "create-object":
            params.update(
                {
                    "object_type": props.object_type,
                    "name": props.object_name or "TestObject",
                },
            )

        elif script == "insert-keyframe":
            params.update(
                {
                    "object_name": props.object_name,
                    "property_name": props.property_name,
                    "frame": props.frame_number,
                    "interpolation": props.interpolation,
                },
            )

        elif script in ["clear-animation", "get-animation-info"]:
            params.update(
                {
                    "object_name": props.object_name,
                },
            )

        elif script == "set-frame-range":
            params.update(
                {
                    "start_frame": props.start_frame,
                    "end_frame": props.end_frame,
                },
            )

        elif script == "animate-along-path":
            params.update(
                {
                    "object_name": props.object_name,
                    "start_frame": props.start_frame,
                    "end_frame": props.end_frame,
                },
            )

        elif script == "render-frame":
            params.update(
                {
                    "frame": props.frame_number,
                },
            )

        return params


class BLENDERMCP_OT_ClearResults(Operator):
    """Clear result display"""

    bl_idname = "blendermcp.clear_results"
    bl_label = "Clear Results"
    bl_description = "Clear execution result display"

    def execute(self, context):
        props = context.scene.blendermcp_test_props
        props.last_result = ""
        return {"FINISHED"}


class BLENDERMCP_OT_SaveTestConfig(Operator):
    """Save test configuration"""

    bl_idname = "blendermcp.save_test_config"
    bl_label = "Save Config"
    bl_description = "Save current test configuration to file"

    def execute(self, context):
        props = context.scene.blendermcp_test_props

        config = {
            "selected_script": props.selected_script,
            "object_name": props.object_name,
            "property_name": props.property_name,
            "frame_number": props.frame_number,
            "start_frame": props.start_frame,
            "end_frame": props.end_frame,
            "object_type": props.object_type,
            "interpolation": props.interpolation,
            "custom_params": props.custom_params,
            "auto_execute": props.auto_execute,
            "show_detailed_result": props.show_detailed_result,
        }

        try:
            import os

            config_path = os.path.join(
                bpy.utils.user_resource("CONFIG"),
                "blendermcp_test_config.json",
            )
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.report({"INFO"}, f"Configuration saved to: {config_path}")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to save configuration: {e!s}")
            return {"CANCELLED"}

        return {"FINISHED"}


class BLENDERMCP_OT_LoadTestConfig(Operator):
    """Load test configuration"""

    bl_idname = "blendermcp.load_test_config"
    bl_label = "Load Config"
    bl_description = "Load test configuration from file"

    def execute(self, context):
        props = context.scene.blendermcp_test_props

        try:
            import os

            config_path = os.path.join(
                bpy.utils.user_resource("CONFIG"),
                "blendermcp_test_config.json",
            )

            if not os.path.exists(config_path):
                self.report({"WARNING"}, "Configuration file does not exist")
                return {"CANCELLED"}

            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            # Apply configuration
            for key, value in config.items():
                if hasattr(props, key):
                    setattr(props, key, value)

            self.report({"INFO"}, "Configuration loaded successfully")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to load configuration: {e!s}")
            return {"CANCELLED"}

        return {"FINISHED"}


class BLENDERMCP_PT_TestPanel(Panel):
    """MCP test panel"""

    bl_label = "MCP Script Tester"
    bl_idname = "BLENDERMCP_PT_TestPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        props = context.scene.blendermcp_test_props

        # Debug: check props object
        if not hasattr(context.scene, "blendermcp_test_props"):
            layout.label(text="Error: Properties not registered", icon="ERROR")
            return

        if props is None:
            layout.label(text="Error: Properties is null", icon="ERROR")
            return

        # Connection status
        box = layout.box()
        row = box.row()
        row.label(text="Connection Status:")
        connection_status = getattr(props, "connection_status", "Not Connected")
        status_text = str(connection_status) if connection_status else "Not Connected"
        row.label(text=status_text)

        # Script selection area
        box = layout.box()
        box.label(text="Script Selection", icon="SCRIPT")

        # Safe access to selected_script property
        if hasattr(props, "selected_script"):
            box.prop(props, "selected_script")
            script = props.selected_script
        else:
            box.label(text="Error: selected_script property not found", icon="ERROR")
            script = "create-object"  # default value

        # Parameter configuration area
        box = layout.box()
        box.label(text="Parameter Configuration", icon="SETTINGS")

        # Show corresponding parameters based on selected script
        if script in ["create-object"]:
            if hasattr(props, "object_type"):
                box.prop(props, "object_type")
            if hasattr(props, "object_name"):
                box.prop(props, "object_name")

        elif script in ["insert-keyframe", "clear-animation", "get-animation-info"]:
            if hasattr(props, "object_name"):
                box.prop(props, "object_name")
            if script == "insert-keyframe":
                if hasattr(props, "property_name"):
                    box.prop(props, "property_name")
                if hasattr(props, "frame_number"):
                    box.prop(props, "frame_number")
                if hasattr(props, "interpolation"):
                    box.prop(props, "interpolation")

        elif script == "set-frame-range":
            row = box.row()
            if hasattr(props, "start_frame"):
                row.prop(props, "start_frame")
            if hasattr(props, "end_frame"):
                row.prop(props, "end_frame")

        elif script == "animate-along-path":
            if hasattr(props, "object_name"):
                box.prop(props, "object_name")
            row = box.row()
            if hasattr(props, "start_frame"):
                row.prop(props, "start_frame")
            if hasattr(props, "end_frame"):
                row.prop(props, "end_frame")

        elif script == "render-frame":
            if hasattr(props, "frame_number"):
                box.prop(props, "frame_number")

        # Custom parameters
        if hasattr(props, "custom_params"):
            box.prop(props, "custom_params")
        else:
            box.label(text="Custom Parameters: Property not found", icon="ERROR")

        # Execution options
        row = box.row()
        if hasattr(props, "auto_execute"):
            row.prop(props, "auto_execute")
        else:
            row.label(text="Auto Execute: Not found", icon="ERROR")

        if hasattr(props, "show_detailed_result"):
            row.prop(props, "show_detailed_result")
        else:
            row.label(text="Detailed Result: Not found", icon="ERROR")

        # Execute button
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("blendermcp.execute_test_script", icon="PLAY")
        row.operator("blendermcp.clear_results", icon="X")

        # Configuration management
        row = layout.row(align=True)
        row.operator("blendermcp.save_test_config", icon="FILE_TICK")
        row.operator("blendermcp.load_test_config", icon="FILE_FOLDER")

        # Result display area
        last_result = getattr(props, "last_result", "")
        # Ensure it's a string value
        result_text = str(last_result) if last_result else ""
        if result_text:
            box = layout.box()
            box.label(text="Execution Result", icon="INFO")

            show_detailed_result = getattr(props, "show_detailed_result", False)
            if show_detailed_result:
                # Multi-line text display
                lines = result_text.split("\n")
                for line in lines[:10]:  # Limit display lines
                    if line.strip():
                        box.label(text=line)
                if len(lines) > 10:
                    box.label(text="... (Result too long, truncated)")
            else:
                box.label(text=result_text)


# Register classes
classes = [
    BLENDERMCP_PG_TestProperties,
    BLENDERMCP_OT_ExecuteTestScript,
    BLENDERMCP_OT_ClearResults,
    BLENDERMCP_OT_SaveTestConfig,
    BLENDERMCP_OT_LoadTestConfig,
    BLENDERMCP_PT_TestPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.blendermcp_test_props = bpy.props.PointerProperty(
        type=BLENDERMCP_PG_TestProperties,
    )


def unregister():
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass

    try:
        del bpy.types.Scene.blendermcp_test_props
    except:
        pass
