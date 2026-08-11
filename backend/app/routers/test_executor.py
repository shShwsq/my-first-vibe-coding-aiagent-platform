import asyncio
import base64
import json
import logging
import time
from typing import Optional, List
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.agent import Agent
from app.models.workflow_agent import WorkflowAgent
from app.models.test_case import TestCase
from app.models.test_case_folder import TestCaseFolder
from app.models.file import BaseFile
from app.models.test_case_image import TestCaseImage
from app.models.extracted_image import ExtractedImage
from app.models.conversation import TestResult, TestConversationState, ChatMessage
from app.routers.unified_agent_chat import call_agent, stream_agent_call, execute_workflow_agent
from app.services.file_storage import file_storage
from app.websocket_manager import manager

logger = logging.getLogger(__name__)


async def get_test_cases_for_folder(db: Session, folder_id: str) -> List[dict]:
    test_cases = db.query(TestCase).filter(
        TestCase.folder_id == folder_id
    ).order_by(TestCase.row_order).all()
    
    results = []
    for tc in test_cases:
        case_data = {
            "id": tc.id,
            "question": tc.question,
            "sample_answer": tc.sample_answer,
            "file_id": tc.file_id,
            "images": []
        }
        
        if tc.file_id:
            test_file = db.query(BaseFile).filter(
                BaseFile.id == tc.file_id
            ).first()
            if test_file:
                case_data["file_path"] = test_file.file_path
                case_data["filename"] = test_file.filename
        
        images = db.query(TestCaseImage).filter(
            TestCaseImage.test_case_id == tc.id
        ).order_by(TestCaseImage.display_order).all()
        
        for img in images:
            case_data["images"].append({
                "image_id": img.image_id,
                "display_order": img.display_order
            })
        
        results.append(case_data)
    
    return results


async def execute_single_test(
    agent: Agent,
    test_case: dict,
    db: Session
) -> dict:
    try:
        question = test_case.get("question", "")
        
        params = {}
        if test_case.get("file_path"):
            params["file_path"] = test_case["file_path"]
        if test_case.get("images"):
            base64_images = []
            for img in test_case["images"]:
                image_id = img.get("image_id")
                if image_id:
                    extracted_image = db.query(ExtractedImage).filter(
                        ExtractedImage.id == image_id
                    ).first()
                    if extracted_image:
                        try:
                            image_data = file_storage.read_image(extracted_image.image_path)
                            img_format = extracted_image.image_format.lower() if extracted_image.image_format else "png"
                            base64_data = base64.b64encode(image_data).decode("utf-8")
                            base64_str = f"data:image/{img_format};base64,{base64_data}"
                            base64_images.append(base64_str)
                        except Exception as e:
                            logger.error(f"Failed to read image {image_id}: {e}")
            if base64_images:
                params["images"] = base64_images
        
        params_to_pass = params if params else None
        
        start_time = time.time()
        
        if agent.response_type == "stream":
            logger.info(f"Using stream mode for agent {agent.name}")
            response_chunks = []
            async for chunk in stream_agent_call(agent, question, params_to_pass):
                response_chunks.append(chunk)
            response = "".join(response_chunks)
        else:
            logger.info(f"Using non-stream mode for agent {agent.name}")
            response = await call_agent(agent, question, params_to_pass)
        
        request_time = time.time() - start_time
        
        return {
            "success": True,
            "response": response,
            "request_time": request_time
        }
    except Exception as e:
        request_time = time.time() - start_time if 'start_time' in dir() else 0
        logger.error(f"Test execution failed for agent {agent.name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error_message": str(e),
            "request_time": request_time
        }


async def execute_single_workflow_test(
    agent: WorkflowAgent,
    test_case: dict,
    db: Session,
    user_id: int
) -> dict:
    try:
        question = test_case.get("question", "")
        
        params = {}
        if test_case.get("file_path"):
            params["file_path"] = test_case["file_path"]
        if test_case.get("images"):
            base64_images = []
            for img in test_case["images"]:
                image_id = img.get("image_id")
                if image_id:
                    extracted_image = db.query(ExtractedImage).filter(
                        ExtractedImage.id == image_id
                    ).first()
                    if extracted_image:
                        try:
                            image_data = file_storage.read_image(extracted_image.image_path)
                            img_format = extracted_image.image_format.lower() if extracted_image.image_format else "png"
                            base64_data = base64.b64encode(image_data).decode("utf-8")
                            base64_str = f"data:image/{img_format};base64,{base64_data}"
                            base64_images.append(base64_str)
                        except Exception as e:
                            logger.error(f"Failed to read image {image_id}: {e}")
            if base64_images:
                params["images"] = base64_images
        
        params_to_pass = params if params else None
        
        start_time = time.time()
        
        logger.info(f"Executing workflow agent {agent.name}")
        result, stream_generator, executor = await execute_workflow_agent(
            agent, question, None, user_id, params_to_pass
        )
        
        if stream_generator:
            response_chunks = []
            async for chunk in stream_generator:
                if chunk:
                    content = None
                    if chunk.startswith("data: "):
                        data_str = chunk[6:]
                        if data_str.strip() and data_str.strip() != "[DONE]":
                            try:
                                data = json.loads(data_str)
                                if isinstance(data.get("content"), str):
                                    content = data["content"]
                            except json.JSONDecodeError:
                                pass
                    else:
                        try:
                            data = json.loads(chunk)
                            if isinstance(data.get("content"), str):
                                content = data["content"]
                        except json.JSONDecodeError:
                            if chunk and not chunk.startswith('{'):
                                content = chunk
                    
                    if content:
                        response_chunks.append(content)
            response = "".join(response_chunks)
        else:
            response = str(result) if result else ""
        
        request_time = time.time() - start_time
        
        return {
            "success": True,
            "response": response,
            "request_time": request_time
        }
    except Exception as e:
        request_time = time.time() - start_time if 'start_time' in dir() else 0
        logger.error(f"Workflow test execution failed for agent {agent.name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error_message": str(e),
            "request_time": request_time
        }


async def save_test_result(
    db: Session,
    agent_id: int,
    test_case_id: str,
    test_folder_id: str,
    question: Optional[str],
    image_ids: Optional[List[str]],
    file_id: Optional[str],
    response: Optional[str],
    error_message: Optional[str],
    request_time: float,
    conversation_id: Optional[int] = None,
    agent_type: str = "agent"
):
    result = TestResult(
        agent_id=agent_id,
        agent_type=agent_type,
        test_case_id=test_case_id,
        test_folder_id=test_folder_id,
        conversation_id=conversation_id,
        question=question,
        image_ids=image_ids,
        file_id=file_id,
        response=response,
        error_message=error_message,
        request_time=request_time
    )
    db.add(result)
    db.commit()
    return result


async def run_test_for_agent(
    agent_id: int,
    folder_id: str,
    user_id: int,
    conversation_id: Optional[int] = None,
    request_interval: int = 0
):
    db = SessionLocal()
    agent = None
    
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            logger.error(f"Agent {agent_id} not found")
            return
        
        folder = db.query(TestCaseFolder).filter(TestCaseFolder.id == folder_id).first()
        if not folder:
            logger.error(f"Test folder {folder_id} not found")
            return
        
        test_cases = await get_test_cases_for_folder(db, folder_id)
        total_cases = len(test_cases)
        
        logger.info(f"Starting test for agent {agent.name} with {total_cases} test cases")
        
        await manager.send_to_user(user_id, {
            "type": "test_progress",
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": "started",
            "total": total_cases,
            "current": 0,
            "message": f"开始测试智能体「{agent.name}」，共 {total_cases} 条测试用例"
        })
        
        success_count = 0
        error_count = 0
        
        for i, test_case in enumerate(test_cases):
            current = i + 1
            question = test_case.get("question", "")[:50] + "..." if len(test_case.get("question", "")) > 50 else test_case.get("question", "")
            
            logger.info(f"Executing test case {current}/{total_cases}: {test_case['id']}")
            
            await manager.send_to_user(user_id, {
                "type": "test_progress",
                "agent_id": agent_id,
                "agent_name": agent.name,
                "status": "testing",
                "total": total_cases,
                "current": current,
                "message": f"正在测试 ({current}/{total_cases}): {question}"
            })
            
            result = await execute_single_test(agent, test_case, db)
            
            if result["success"]:
                success_count += 1
            else:
                error_count += 1
            
            image_ids = [img.get("image_id") for img in test_case.get("images", []) if img.get("image_id")]
            
            await save_test_result(
                db=db,
                agent_id=agent_id,
                agent_type="agent",
                test_case_id=test_case["id"],
                test_folder_id=folder_id,
                question=test_case.get("question"),
                image_ids=image_ids if image_ids else None,
                file_id=test_case.get("file_id"),
                response=result.get("response") if result["success"] else None,
                error_message=result.get("error_message") if not result["success"] else None,
                request_time=result["request_time"],
                conversation_id=conversation_id
            )
            
            if i < total_cases - 1 and request_interval > 0:
                logger.info(f"Waiting {request_interval} seconds before next test...")
                await asyncio.sleep(request_interval)
        
        logger.info(f"Test completed for agent {agent.name}")
        
        await manager.send_to_user(user_id, {
            "type": "test_progress",
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": "completed",
            "total": total_cases,
            "current": total_cases,
            "success_count": success_count,
            "error_count": error_count,
            "message": f"智能体「{agent.name}」测试完成，成功 {success_count} 条，失败 {error_count} 条"
        })
        
    except Exception as e:
        logger.error(f"Test execution error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        await manager.send_to_user(user_id, {
            "type": "test_progress",
            "agent_id": agent_id,
            "agent_name": agent.name if agent else f"Agent {agent_id}",
            "status": "error",
            "message": f"测试出错: {str(e)}"
        })
    finally:
        db.close()


async def run_test_for_workflow_agent(
    agent_id: int,
    folder_id: str,
    user_id: int,
    conversation_id: Optional[int] = None,
    request_interval: int = 0
):
    db = SessionLocal()
    agent = None
    
    try:
        agent = db.query(WorkflowAgent).filter(WorkflowAgent.id == agent_id).first()
        if not agent:
            logger.error(f"Workflow Agent {agent_id} not found")
            return
        
        folder = db.query(TestCaseFolder).filter(TestCaseFolder.id == folder_id).first()
        if not folder:
            logger.error(f"Test folder {folder_id} not found")
            return
        
        test_cases = await get_test_cases_for_folder(db, folder_id)
        total_cases = len(test_cases)
        
        logger.info(f"Starting test for workflow agent {agent.name} with {total_cases} test cases")
        
        await manager.send_to_user(user_id, {
            "type": "test_progress",
            "agent_id": agent_id,
            "agent_name": agent.name,
            "agent_type": "workflow",
            "status": "started",
            "total": total_cases,
            "current": 0,
            "message": f"开始测试工作流智能体「{agent.name}」，共 {total_cases} 条测试用例"
        })
        
        success_count = 0
        error_count = 0
        
        for i, test_case in enumerate(test_cases):
            current = i + 1
            question = test_case.get("question", "")[:50] + "..." if len(test_case.get("question", "")) > 50 else test_case.get("question", "")
            
            logger.info(f"Executing test case {current}/{total_cases}: {test_case['id']}")
            
            await manager.send_to_user(user_id, {
                "type": "test_progress",
                "agent_id": agent_id,
                "agent_name": agent.name,
                "agent_type": "workflow",
                "status": "testing",
                "total": total_cases,
                "current": current,
                "message": f"正在测试 ({current}/{total_cases}): {question}"
            })
            
            result = await execute_single_workflow_test(agent, test_case, db, user_id)
            
            if result["success"]:
                success_count += 1
            else:
                error_count += 1
            
            image_ids = [img.get("image_id") for img in test_case.get("images", []) if img.get("image_id")]
            
            await save_test_result(
                db=db,
                agent_id=agent_id,
                agent_type="workflow_agent",
                test_case_id=test_case["id"],
                test_folder_id=folder_id,
                question=test_case.get("question"),
                image_ids=image_ids if image_ids else None,
                file_id=test_case.get("file_id"),
                response=result.get("response") if result["success"] else None,
                error_message=result.get("error_message") if not result["success"] else None,
                request_time=result["request_time"],
                conversation_id=conversation_id
            )
            
            if i < total_cases - 1 and request_interval > 0:
                logger.info(f"Waiting {request_interval} seconds before next test...")
                await asyncio.sleep(request_interval)
        
        logger.info(f"Test completed for workflow agent {agent.name}")
        
        await manager.send_to_user(user_id, {
            "type": "test_progress",
            "agent_id": agent_id,
            "agent_name": agent.name,
            "agent_type": "workflow",
            "status": "completed",
            "total": total_cases,
            "current": total_cases,
            "success_count": success_count,
            "error_count": error_count,
            "message": f"工作流智能体「{agent.name}」测试完成，成功 {success_count} 条，失败 {error_count} 条"
        })
        
    except Exception as e:
        logger.error(f"Workflow test execution error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        await manager.send_to_user(user_id, {
            "type": "test_progress",
            "agent_id": agent_id,
            "agent_name": agent.name if agent else f"Workflow Agent {agent_id}",
            "agent_type": "workflow",
            "status": "error",
            "message": f"测试出错: {str(e)}"
        })
    finally:
        db.close()


async def run_tests_for_multiple_agents(
    agent_ids: List[int],
    folder_id: str,
    user_id: int,
    conversation_id: Optional[int] = None,
    request_interval: int = 0,
    workflow_agent_ids: Optional[List[int]] = None
):
    db = SessionLocal()
    
    try:
        folder = db.query(TestCaseFolder).filter(TestCaseFolder.id == folder_id).first()
        folder_name = folder.name if folder else ""
        
        test_cases = await get_test_cases_for_folder(db, folder_id)
        total_cases = len(test_cases)
        
        agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all() if agent_ids else []
        agent_names = [a.name for a in agents]
        
        workflow_agents = db.query(WorkflowAgent).filter(WorkflowAgent.id.in_(workflow_agent_ids)).all() if workflow_agent_ids else []
        workflow_agent_names = [a.name for a in workflow_agents]
        
        all_agent_names = agent_names + workflow_agent_names
        total_agent_count = len(agents) + len(workflow_agents)
        
        await manager.send_to_user(user_id, {
            "type": "test_all_started",
            "agent_ids": agent_ids,
            "agent_names": all_agent_names,
            "folder_name": folder_name,
            "total_cases": total_cases,
            "message": f"开始测试 {total_agent_count} 个智能体，共 {total_cases} 条测试用例"
        })
        
        tasks = [
            run_test_for_agent(agent_id, folder_id, user_id, conversation_id, request_interval)
            for agent_id in (agent_ids or [])
        ]
        
        tasks.extend([
            run_test_for_workflow_agent(agent_id, folder_id, user_id, conversation_id, request_interval)
            for agent_id in (workflow_agent_ids or [])
        ])
        
        await asyncio.gather(*tasks)
        
        if conversation_id:
            test_state = db.query(TestConversationState).filter(
                TestConversationState.conversation_id == conversation_id
            ).first()
            if test_state:
                test_state.status = "completed"
            
            completion_message = ChatMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=f"测试完成！已测试 {total_agent_count} 个智能体，每个智能体 {total_cases} 条测试用例。"
            )
            db.add(completion_message)
            db.commit()
        
        await manager.send_to_user(user_id, {
            "type": "test_all_completed",
            "agent_ids": agent_ids,
            "agent_names": all_agent_names,
            "folder_name": folder_name,
            "total_cases": total_cases,
            "message": f"所有测试完成！已测试 {total_agent_count} 个智能体，每个智能体 {total_cases} 条测试用例。"
        })
        
    except Exception as e:
        logger.error(f"Multi-agent test error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        if conversation_id:
            test_state = db.query(TestConversationState).filter(
                TestConversationState.conversation_id == conversation_id
            ).first()
            if test_state:
                test_state.status = "error"
            
            error_message = ChatMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=f"测试出错: {str(e)}"
            )
            db.add(error_message)
            db.commit()
        
        await manager.send_to_user(user_id, {
            "type": "test_all_error",
            "message": f"测试出错: {str(e)}"
        })
    finally:
        db.close()
