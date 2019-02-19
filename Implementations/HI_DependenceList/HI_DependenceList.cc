#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Pass.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"
#include "HI_print.h"
#include "HI_DependenceList.h"
#include <stdio.h>
#include <string>
#include <ios>
#include <stdlib.h>

using namespace llvm;

bool HI_DependenceList::runOnFunction(Function &F) // The runOnModule declaration will overide the virtual one in ModulePass, which will be executed for each Module.
{
    if (Function_id.find(&F)==Function_id.end())  // traverse functions and assign function ID
    {
        Function_id[&F] = ++Function_Counter;
    }
    for (BasicBlock &B : F) 
    {
        if (BasicBlock_id.find(&B)==BasicBlock_id.end())  // traverse blocks in the function and assign basic block ID
        {
            BasicBlock_id[&B] = ++BasicBlock_Counter;
        }

        *Instruction_out << "\n B-ID: " << B.getName() << "\n";
        *Dependence_out << "\n\n\n\n B-ID: " << B.getName() << "\n";
        *Dependence_out << "==============================\n";

        // check the relation between blocks and map them
        checkPredecessorsOfBlock(&B);
        checkSuccessorsOfBlock(&B);

        *Dependence_out << "\n==============================\n";
        for (Instruction &I: B) 
        {
            // handle the dependence of current instruction
            checkInstructionDependence(&I);
        }
    }
    return false;
}



char HI_DependenceList::ID = 0;  // the ID for pass should be initialized but the value does not matter, since LLVM uses the address of this variable as label instead of its value.

void HI_DependenceList::getAnalysisUsage(AnalysisUsage &AU) const {
  AU.setPreservesAll();
}

void HI_DependenceList::checkSuccessorsOfBlock(BasicBlock *B)
{
    assert(Block_Successors.find(B) == Block_Successors.end() && "This Block should not be checked before" );
    *Dependence_out << "\nTerminator: "<<*(B->getTerminator()) <<"\n";
    *Dependence_out << "Successor(s) are: ";

    std::vector<BasicBlock*>* tmp_vec = new std::vector<BasicBlock*>;

    for (auto Succ_it : successors(B))
    {
        *Dependence_out << Succ_it->getName()  << "--";
        tmp_vec->push_back(Succ_it);
    }   
    Block_Successors[B] = tmp_vec;
}

void HI_DependenceList::checkPredecessorsOfBlock(BasicBlock *B)
{
    assert(Block_Predecessors.find(B) == Block_Predecessors.end() && "This Block should not be checked before" );
    *Dependence_out << "Predecessor(s) are: ";
    std::vector<BasicBlock*>* tmp_vec = new std::vector<BasicBlock*>;
    for (auto PreB_it: predecessors(B))
    {
        *Dependence_out << PreB_it->getName() << "--";
        tmp_vec->push_back(PreB_it);
    }    
    Block_Predecessors[B] = tmp_vec;
}

void HI_DependenceList::checkInstructionDependence(Instruction *I)
{
    if (Instruction_id.find(I)==Instruction_id.end()) // traverse instructions in the block assign instruction ID
    {
        Instruction_id[I] = ++Instruction_Counter;
    }

    *Instruction_out << "  I-ID: " << Instruction_id[I] <<  " Instruction: "  << *I << "\n";


    std::vector<int> *tmp_vec_id;
    if (Instruction2User_id.find(Instruction_id[I]) == Instruction2User_id.end())   // new a vector to store users
    {
        tmp_vec_id = new std::vector<int>;
        Instruction2User_id[Instruction_id[I]] = tmp_vec_id;
    }
    else
    {
        tmp_vec_id = Instruction2User_id[Instruction_id[I]];
    }
    

    *Dependence_out << "  I" << Instruction_id[I] <<  ": "  << *I << "--> " ;
    for (User *U : (I)->users()) // find the users of the instruction and insert them into map
    {        
        if (Instruction *Suc_Inst = dyn_cast<Instruction>(U)) 
        {
            if (Instruction_id.find(Suc_Inst)==Instruction_id.end())
            {
                Instruction_id[Suc_Inst] = ++Instruction_Counter;
            }
            tmp_vec_id->push_back(Instruction_id[Suc_Inst]);
            *Dependence_out << Instruction_id[Suc_Inst] << " ";


            std::vector<int> *tmp_vec_id_1;   // add the instruction in the other instruction's presessor list
            if (Instruction2Pre_id.find(Instruction_id[Suc_Inst]) == Instruction2Pre_id.end())
            {
                tmp_vec_id_1 = new std::vector<int>;
                Instruction2Pre_id[Instruction_id[Suc_Inst]] = tmp_vec_id_1;
            }
            else
            {
                tmp_vec_id_1 = Instruction2Pre_id[Instruction_id[Suc_Inst]];
            }
            tmp_vec_id_1->push_back(Instruction_id[I]);
        }
    }
    *Dependence_out << "\n";
}